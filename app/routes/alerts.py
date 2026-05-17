from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.alert import AlertRead
from app.services.alert_service import list_alerts

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertRead])
def get_alerts(db: Session = Depends(get_db)):
    return list_alerts(db)


@router.get("/patients/{patient_id}/alerts", response_model=list[AlertRead])
def get_patient_alerts(patient_id: str, db: Session = Depends(get_db)):
    return list_alerts(db, patient_id)

