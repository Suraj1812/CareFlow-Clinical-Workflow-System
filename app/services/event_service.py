from sqlalchemy.orm import Session

from app.models.entities import EventLedger
from app.utils.ids import new_id


def append_event(db: Session, aggregate_id: str, event_type: str, payload: dict) -> EventLedger:
    event = EventLedger(
        event_id=new_id("EVT"),
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event

