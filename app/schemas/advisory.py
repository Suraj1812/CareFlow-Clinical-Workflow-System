from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.validation import parse_hhmm


class AdvisoryCreate(BaseModel):
    patient_id: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    clinician_name: str = Field(..., min_length=2, max_length=120)
    instruction: str = Field(..., min_length=5, max_length=1000)
    schedule_type: Literal["daily", "weekly"]
    time: str = Field(..., examples=["08:00"])

    @field_validator("patient_id", mode="before")
    @classmethod
    def empty_patient_id_is_generated(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return parse_hhmm(value)


class AdvisoryRead(BaseModel):
    advisory_id: str
    patient_id: str
    clinician_name: str
    instruction: str
    schedule_type: str
    time: str
    created_at: datetime


class AdvisoryCreateResponse(BaseModel):
    advisory: AdvisoryRead
    schedules: list["ScheduleRead"]
    event_ids: list[str]


from app.schemas.schedule import ScheduleRead  # noqa: E402

AdvisoryCreateResponse.model_rebuild()
