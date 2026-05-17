from datetime import datetime

from pydantic import BaseModel


class ScheduleRead(BaseModel):
    schedule_id: str
    advisory_id: str
    patient_id: str
    task: str
    scheduled_time: datetime
    status: str

