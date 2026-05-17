import logging

from fastapi import status
from sqlalchemy.orm import Session

from app.models.entities import Alert, PatientResponse, Schedule
from app.rules.engine import RuleResult, evaluate_missed_schedules, evaluate_observation
from app.schemas.alert import AlertRead
from app.schemas.response import PatientResponseCreate, PatientResponseCreateResponse, PatientResponseRead
from app.services.event_service import append_event
from app.services.schedule_service import mark_overdue_schedules_missed
from app.utils.errors import DomainError
from app.utils.ids import new_id
from app.utils.time import utc_now

logger = logging.getLogger("careflow.responses")


def _response_read(response: PatientResponse) -> PatientResponseRead:
    return PatientResponseRead(
        response_id=response.response_id,
        patient_id=response.patient_id,
        schedule_id=response.schedule_id,
        observation_type=response.observation_type,
        value=response.value,
        created_at=response.created_at,
    )


def _alert_read(alert: Alert) -> AlertRead:
    return AlertRead(
        alert_id=alert.alert_id,
        patient_id=alert.patient_id,
        severity=alert.severity,
        reason=alert.reason,
        created_at=alert.created_at,
    )


def _create_alert(db: Session, patient_id: str, result: RuleResult, source_event_id: str) -> tuple[Alert, str]:
    alert = Alert(
        alert_id=new_id("ALT"),
        patient_id=patient_id,
        severity=result.severity,
        reason=f"{result.reason} Rule: {result.rule_id}.",
        source_event_id=source_event_id,
    )
    db.add(alert)
    db.flush()
    alert_event = append_event(
        db,
        aggregate_id=alert.alert_id,
        event_type="alert_triggered",
        payload={
            "alert_id": alert.alert_id,
            "patient_id": patient_id,
            "severity": alert.severity,
            "reason": alert.reason,
            "source_event_id": source_event_id,
        },
    )
    logger.info(
        "alert_triggered",
        extra={"alert_id": alert.alert_id, "patient_id": patient_id, "severity": alert.severity},
    )
    return alert, alert_event.event_id


def record_response(db: Session, payload: PatientResponseCreate) -> PatientResponseCreateResponse:
    schedule = db.query(Schedule).filter(Schedule.schedule_id == payload.schedule_id).one_or_none()
    if schedule is None:
        raise DomainError("Schedule was not found.", status.HTTP_404_NOT_FOUND)
    if schedule.patient_id != payload.patient_id:
        raise DomainError("Schedule does not belong to the supplied patient.", status.HTTP_409_CONFLICT)

    mark_overdue_schedules_missed(db, payload.patient_id)

    response = PatientResponse(
        response_id=new_id("RSP"),
        patient_id=payload.patient_id,
        schedule_id=payload.schedule_id,
        observation_type=payload.observation_type,
        value=payload.value,
    )
    db.add(response)

    schedule.status = "completed"
    schedule.completed_at = utc_now()
    db.flush()

    response_event = append_event(
        db,
        aggregate_id=response.response_id,
        event_type="response_recorded",
        payload={
            "response_id": response.response_id,
            "patient_id": response.patient_id,
            "schedule_id": response.schedule_id,
            "observation_type": response.observation_type,
            "value": response.value,
        },
    )

    rule_results = evaluate_observation(payload.observation_type, payload.value)
    missed_count = (
        db.query(Schedule)
        .filter(Schedule.patient_id == payload.patient_id, Schedule.status == "missed")
        .count()
    )
    rule_results.extend(evaluate_missed_schedules(missed_count))

    alert_pairs = [_create_alert(db, payload.patient_id, result, response_event.event_id) for result in rule_results]
    alerts = [alert for alert, _ in alert_pairs]

    logger.info(
        "response_recorded",
        extra={"response_id": response.response_id, "patient_id": response.patient_id},
    )

    db.refresh(response)
    for alert in alerts:
        db.refresh(alert)

    event_ids = [response_event.event_id]
    event_ids.extend(event_id for _, event_id in alert_pairs)
    return PatientResponseCreateResponse(
        response=_response_read(response),
        alerts=[_alert_read(alert) for alert in alerts],
        event_ids=event_ids,
    )


def list_responses(db: Session, patient_id: str | None = None) -> list[PatientResponseRead]:
    query = db.query(PatientResponse)
    if patient_id:
        query = query.filter(PatientResponse.patient_id == patient_id)
    responses = query.order_by(PatientResponse.created_at.desc(), PatientResponse.id.desc()).limit(100).all()
    return [_response_read(response) for response in responses]
