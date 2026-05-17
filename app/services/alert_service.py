from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.entities import Alert
from app.schemas.alert import AlertRead


def _alert_read(alert: Alert) -> AlertRead:
    return AlertRead(
        alert_id=alert.alert_id,
        patient_id=alert.patient_id,
        severity=alert.severity,
        reason=alert.reason,
        created_at=alert.created_at,
    )


def list_alerts(db: Session, patient_id: str | None = None, q: str | None = None) -> list[AlertRead]:
    query = db.query(Alert)
    if patient_id:
        query = query.filter(Alert.patient_id == patient_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Alert.alert_id.ilike(term),
                Alert.patient_id.ilike(term),
                Alert.severity.ilike(term),
                Alert.reason.ilike(term),
            )
        )
    alerts = query.order_by(Alert.created_at.desc(), Alert.id.desc()).all()
    return [_alert_read(alert) for alert in alerts]
