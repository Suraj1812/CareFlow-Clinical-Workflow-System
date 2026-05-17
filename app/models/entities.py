from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EventLedger(Base):
    __tablename__ = "event_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)


class Advisory(Base):
    __tablename__ = "advisories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    advisory_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    clinician_name: Mapped[str] = mapped_column(String(120), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_time: Mapped[str] = mapped_column(String(5), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    schedules: Mapped[list["Schedule"]] = relationship(back_populates="advisory")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    schedule_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    advisory_id: Mapped[str] = mapped_column(String(32), ForeignKey("advisories.advisory_id"), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    advisory: Mapped[Advisory] = relationship(back_populates="schedules")


class PatientResponse(Base):
    __tablename__ = "patient_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    response_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    schedule_id: Mapped[str] = mapped_column(String(32), ForeignKey("schedules.schedule_id"), index=True, nullable=False)
    observation_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)


def _prevent_event_ledger_mutation(mapper, connection, target) -> None:
    raise RuntimeError("Event ledger rows are append-only and cannot be changed.")


event.listen(EventLedger, "before_update", _prevent_event_ledger_mutation)
event.listen(EventLedger, "before_delete", _prevent_event_ledger_mutation)
