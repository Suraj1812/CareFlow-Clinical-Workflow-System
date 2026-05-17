from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.advisory import AdvisoryCreate, AdvisoryCreateResponse, AdvisoryRead
from app.services import advisory_service, idempotency_service
from app.utils.errors import DomainError

router = APIRouter(tags=["advisories"])


@router.post("/advisories", response_model=AdvisoryCreateResponse, status_code=status.HTTP_201_CREATED)
def create_advisory(
    payload: AdvisoryCreate,
    response: Response,
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
        result = advisory_service.publish_advisory(db, payload)
        body = result.model_dump(mode="json")
        if idempotency_key:
            idempotency_service.store_response(db, idempotency_key, payload_hash, body, status.HTTP_201_CREATED)
        db.commit()
        return body
    except Exception:
        db.rollback()
        raise


@router.get("/advisories", response_model=list[AdvisoryRead])
def list_advisories(db: Session = Depends(get_db)):
    return advisory_service.list_advisories(db)


@router.get("/advisories/{advisory_id}", response_model=AdvisoryCreateResponse)
def get_advisory(advisory_id: str, db: Session = Depends(get_db)):
    result = advisory_service.get_advisory(db, advisory_id)
    if result is None:
        raise DomainError("Advisory was not found.", status.HTTP_404_NOT_FOUND)
    return result

