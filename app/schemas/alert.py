from datetime import datetime

from pydantic import BaseModel


class AlertRead(BaseModel):
    alert_id: str
    patient_id: str
    severity: str
    reason: str
    created_at: datetime

