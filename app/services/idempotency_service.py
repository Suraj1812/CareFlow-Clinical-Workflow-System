import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import IdempotencyRecord
from app.utils.errors import IdempotencyConflict


def request_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_cached_response(db: Session, idempotency_key: str, payload_hash: str) -> IdempotencyRecord | None:
    record = (
        db.query(IdempotencyRecord)
        .filter(IdempotencyRecord.idempotency_key == idempotency_key)
        .one_or_none()
    )
    if record is None:
        return None
    if record.request_hash != payload_hash:
        raise IdempotencyConflict()
    return record


def store_response(
    db: Session,
    idempotency_key: str,
    payload_hash: str,
    response_body: dict[str, Any],
    status_code: int,
) -> IdempotencyRecord:
    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        request_hash=payload_hash,
        response_body=response_body,
        status_code=status_code,
    )
    db.add(record)
    db.flush()
    return record

