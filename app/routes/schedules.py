from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.schedule import ScheduleRead
from app.services.advisory_service import _schedule_read
from app.services.schedule_service import list_patient_schedule

router = APIRouter(tags=["schedules"])


@router.get("/patients/{patient_id}/schedule", response_model=list[ScheduleRead])
def get_patient_schedule(patient_id: str, q: str | None = None, db: Session = Depends(get_db)):
    schedules = list_patient_schedule(db, patient_id, q)
    db.commit()
    return [_schedule_read(schedule) for schedule in schedules]
