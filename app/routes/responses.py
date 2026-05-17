from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import PatientResponseCreate, PatientResponseCreateResponse, PatientResponseRead
from app.services import idempotency_service, response_service

router = APIRouter(tags=["responses"])


@router.post("/responses", response_model=PatientResponseCreateResponse, status_code=status.HTTP_201_CREATED)
def create_response(
    payload: PatientResponseCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    payload_body = payload.model_dump(mode="json")
    payload_hash = idempotency_service.request_hash(payload_body)

    if idempotency_key:
        cached = idempotency_service.get_cached_response(db, idempotency_key, payload_hash)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response_body)

    try:
        result = response_service.record_response(db, payload)
        body = result.model_dump(mode="json")
        if idempotency_key:
            idempotency_service.store_response(db, idempotency_key, payload_hash, body, status.HTTP_201_CREATED)
        db.commit()
        return body
    except Exception:
        db.rollback()
        raise


@router.get("/responses", response_model=list[PatientResponseRead])
def list_responses(patient_id: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    return response_service.list_responses(db, patient_id, q)
