from pydantic import ValidationError
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entities import Advisory, Schedule
from app.schemas.advisory import AdvisoryCreate
from app.schemas.response import PatientResponseCreate
from app.services import advisory_service, response_service
from app.services.alert_service import list_alerts
from app.services.schedule_service import list_patient_schedule

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


def _render(request: Request, template_name: str, context: dict):
    base_context = {"request": request}
    base_context.update(context)
    return templates.TemplateResponse(template_name, base_context)


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    advisories = advisory_service.list_advisories(db)[:10]
    return _render(request, "advisory_form.html", {"advisories": advisories, "error": None})


@router.get("/ui/advisories")
def ui_advisories(request: Request, db: Session = Depends(get_db)):
    advisories = advisory_service.list_advisories(db)
    return _render(request, "advisories.html", {"advisories": advisories})


@router.post("/ui/advisories")
def ui_create_advisory(
    request: Request,
    patient_id: str = Form(...),
    clinician_name: str = Form(...),
    instruction: str = Form(...),
    schedule_type: str = Form(...),
    time: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        payload = AdvisoryCreate(
            patient_id=patient_id,
            clinician_name=clinician_name,
            instruction=instruction,
            schedule_type=schedule_type,
            time=time,
        )
        result = advisory_service.publish_advisory(db, payload)
        db.commit()
    except (ValidationError, ValueError) as exc:
        db.rollback()
        advisories = advisory_service.list_advisories(db)[:10]
        return _render(
            request,
            "advisory_form.html",
            {
                "advisories": advisories,
                "error": "Please check the advisory fields and submit again.",
                "form": {
                    "patient_id": patient_id,
                    "clinician_name": clinician_name,
                    "instruction": instruction,
                    "schedule_type": schedule_type,
                    "time": time,
                },
            },
        )
    return RedirectResponse(
        url=f"/ui/advisories/{result.advisory.advisory_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/ui/advisories/{advisory_id}")
def ui_advisory_detail(advisory_id: str, request: Request, db: Session = Depends(get_db)):
    result = advisory_service.get_advisory(db, advisory_id)
    if result is None:
        return _render(request, "not_found.html", {"message": "Advisory was not found."})
    return _render(request, "advisory_detail.html", {"result": result})


@router.get("/ui/schedule")
def ui_schedule(request: Request, patient_id: str | None = None, db: Session = Depends(get_db)):
    schedules = []
    if patient_id:
        schedules = list_patient_schedule(db, patient_id)
        db.commit()
    return _render(
        request,
        "schedule.html",
        {
            "patient_id": patient_id or "",
            "schedules": schedules,
        },
    )


@router.get("/ui/responses")
def ui_responses(request: Request, patient_id: str | None = None, db: Session = Depends(get_db)):
    schedules = []
    if patient_id:
        schedules = list_patient_schedule(db, patient_id)
        db.commit()
    responses = response_service.list_responses(db, patient_id)
    return _render(
        request,
        "responses.html",
        {
            "patient_id": patient_id or "",
            "schedules": schedules,
            "responses": responses,
            "error": None,
        },
    )


@router.post("/ui/responses")
def ui_create_response(
    request: Request,
    patient_id: str = Form(...),
    schedule_id: str = Form(...),
    observation_type: str = Form(...),
    value: float = Form(...),
    db: Session = Depends(get_db),
):
    try:
        payload = PatientResponseCreate(
            patient_id=patient_id,
            schedule_id=schedule_id,
            observation_type=observation_type,
            value=value,
        )
        response_service.record_response(db, payload)
        db.commit()
    except Exception:
        db.rollback()
        schedules = list_patient_schedule(db, patient_id)
        responses = response_service.list_responses(db, patient_id)
        return _render(
            request,
            "responses.html",
            {
                "patient_id": patient_id,
                "schedules": schedules,
                "responses": responses,
                "error": "Response could not be recorded. Confirm the patient and schedule values.",
            },
        )
    return RedirectResponse(url=f"/ui/responses?patient_id={patient_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/ui/alerts")
def ui_alerts(request: Request, patient_id: str | None = None, db: Session = Depends(get_db)):
    alerts = list_alerts(db, patient_id)
    return _render(request, "alerts.html", {"alerts": alerts, "patient_id": patient_id or ""})

