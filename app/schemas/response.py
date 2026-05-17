from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.alert import AlertRead


class PatientResponseCreate(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    schedule_id: str = Field(..., min_length=1, max_length=32)
    observation_type: Literal["blood_sugar", "heart_rate", "temperature", "oxygen_saturation"]
    value: float = Field(..., ge=0)


class PatientResponseRead(BaseModel):
    response_id: str
    patient_id: str
    schedule_id: str
    observation_type: str
    value: float
    created_at: datetime


class PatientResponseCreateResponse(BaseModel):
    response: PatientResponseRead
    alerts: list[AlertRead]
    event_ids: list[str]

