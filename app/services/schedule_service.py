from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Schedule
from app.utils.ids import new_id
from app.utils.time import utc_now
from app.utils.validation import parse_hhmm


def _next_start(schedule_time: str, now: datetime | None = None) -> datetime:
    now = now or utc_now()
    hour, minute = map(int, parse_hhmm(schedule_time).split(":"))
    candidate = datetime.combine(now.date(), time(hour=hour, minute=minute))
    if candidate < now:
        candidate += timedelta(days=1)
    return candidate


def build_schedule_entries(
    advisory_id: str,
    patient_id: str,
    instruction: str,
    schedule_type: str,
    schedule_time: str,
    now: datetime | None = None,
) -> list[Schedule]:
    first_run = _next_start(schedule_time, now)
    count = 7 if schedule_type == "daily" else 4
    step = timedelta(days=1 if schedule_type == "daily" else 7)

    return [
        Schedule(
            schedule_id=new_id("SCH"),
            advisory_id=advisory_id,
            patient_id=patient_id,
            task=instruction,
            scheduled_time=first_run + (step * index),
            status="pending",
        )
        for index in range(count)
    ]


def mark_overdue_schedules_missed(db: Session, patient_id: str, now: datetime | None = None) -> int:
    now = now or utc_now()
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.patient_id == patient_id,
            Schedule.status == "pending",
            Schedule.scheduled_time < now,
        )
        .all()
    )
    for schedule in schedules:
        schedule.status = "missed"
    if schedules:
        db.flush()
    return len(schedules)


def list_patient_schedule(db: Session, patient_id: str) -> list[Schedule]:
    mark_overdue_schedules_missed(db, patient_id)
    return (
        db.query(Schedule)
        .filter(Schedule.patient_id == patient_id)
        .order_by(Schedule.scheduled_time.asc())
        .all()
    )
