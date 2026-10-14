from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user, doctor_user, admin_user
from app.models import User
from app.services.appointments import dashboard as dashboard_service
from app.services.common import get_doctor
from app.schemas import AppointmentPublic

router = APIRouter(tags=["dashboards"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    data = dashboard_service(db, user)
    result = dict(data)
    result["recent_appointments"] = [AppointmentPublic.model_validate(a).model_dump(mode="json") for a in data["recent_appointments"]]
    return result


@router.get("/doctors/me/analytics")
def doctor_analytics(db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    data = dashboard_service(db, user)
    return {"dashData": {"appointments": sum(data["appointment_counts"].values()), "completedAppointments": data["appointment_counts"].get("completed", 0), "upcomingAppointments": data["upcoming_count"], "patients": data["patient_count"], "earnings": float(data["completed_earnings"]), "latestAppointments": [AppointmentPublic.model_validate(a).model_dump(mode="json") for a in data["recent_appointments"]]}}
