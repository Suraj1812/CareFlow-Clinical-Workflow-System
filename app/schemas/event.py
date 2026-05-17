from datetime import datetime

from pydantic import BaseModel


class EventRead(BaseModel):
    event_id: str
    aggregate_id: str
    event_type: str
    payload: dict
    created_at: datetime

