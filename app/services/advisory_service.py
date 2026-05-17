import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.entities import Advisory
from app.schemas.advisory import AdvisoryCreate, AdvisoryCreateResponse, AdvisoryRead
from app.schemas.schedule import ScheduleRead
from app.services.event_service import append_event
from app.services.schedule_service import build_schedule_entries
from app.utils.ids import new_id, new_patient_id

logger = logging.getLogger("careflow.advisories")


def generate_patient_id(db: Session) -> str:
    for _ in range(10):
        patient_id = new_patient_id()
        exists = db.query(Advisory.id).filter(Advisory.patient_id == patient_id).first()
        if not exists:
            return patient_id
    return new_patient_id()


def _advisory_read(advisory: Advisory) -> AdvisoryRead:
    return AdvisoryRead(
        advisory_id=advisory.advisory_id,
        patient_id=advisory.patient_id,
        clinician_name=advisory.clinician_name,
        instruction=advisory.instruction,
        schedule_type=advisory.schedule_type,
        time=advisory.schedule_time,
        created_at=advisory.created_at,
    )


def _schedule_read(schedule) -> ScheduleRead:
    return ScheduleRead(
        schedule_id=schedule.schedule_id,
        advisory_id=schedule.advisory_id,
        patient_id=schedule.patient_id,
        task=schedule.task,
        scheduled_time=schedule.scheduled_time,
        status=schedule.status,
    )


def publish_advisory(db: Session, payload: AdvisoryCreate) -> AdvisoryCreateResponse:
    patient_id = payload.patient_id or generate_patient_id(db)
    advisory = Advisory(
        advisory_id=new_id("ADV"),
        patient_id=patient_id,
        clinician_name=payload.clinician_name,
        instruction=payload.instruction,
        schedule_type=payload.schedule_type,
        schedule_time=payload.time,
    )
    db.add(advisory)
    db.flush()

    advisory_event = append_event(
        db,
        aggregate_id=advisory.advisory_id,
        event_type="advisory_created",
        payload={
            "advisory_id": advisory.advisory_id,
            "patient_id": advisory.patient_id,
            "clinician_name": advisory.clinician_name,
            "instruction": advisory.instruction,
            "schedule_type": advisory.schedule_type,
            "time": advisory.schedule_time,
        },
    )

    schedules = build_schedule_entries(
        advisory_id=advisory.advisory_id,
        patient_id=advisory.patient_id,
        instruction=advisory.instruction,
        schedule_type=advisory.schedule_type,
        schedule_time=advisory.schedule_time,
    )
    db.add_all(schedules)
    db.flush()

    schedule_event = append_event(
        db,
        aggregate_id=advisory.advisory_id,
        event_type="schedule_generated",
        payload={
            "advisory_id": advisory.advisory_id,
            "patient_id": advisory.patient_id,
            "schedule_ids": [schedule.schedule_id for schedule in schedules],
        },
    )

    logger.info(
        "advisory_created",
        extra={"advisory_id": advisory.advisory_id, "patient_id": advisory.patient_id},
    )

    db.refresh(advisory)
    for schedule in schedules:
        db.refresh(schedule)

    return AdvisoryCreateResponse(
        advisory=_advisory_read(advisory),
        schedules=[_schedule_read(schedule) for schedule in schedules],
        event_ids=[advisory_event.event_id, schedule_event.event_id],
    )


def list_advisories(db: Session, q: str | None = None) -> list[AdvisoryRead]:
    query = db.query(Advisory)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Advisory.advisory_id.ilike(term),
                Advisory.patient_id.ilike(term),
                Advisory.clinician_name.ilike(term),
                Advisory.instruction.ilike(term),
                Advisory.schedule_type.ilike(term),
            )
        )
    advisories = query.order_by(Advisory.created_at.desc(), Advisory.id.desc()).all()
    return [_advisory_read(advisory) for advisory in advisories]


def get_advisory(db: Session, advisory_id: str) -> AdvisoryCreateResponse | None:
    advisory = db.query(Advisory).filter(Advisory.advisory_id == advisory_id).one_or_none()
    if advisory is None:
        return None
    return AdvisoryCreateResponse(
        advisory=_advisory_read(advisory),
        schedules=[_schedule_read(schedule) for schedule in advisory.schedules],
        event_ids=[],
    )
