from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import admin_user
from app.models import User
from app.schemas import AdminDoctorCreate
from app.services import admin as service
from app.api.v1.endpoints.doctors import serialize as serialize_doctor

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_user)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {"dashData": service.summary(db)}


@router.get("/doctors")
def doctors(db: Session = Depends(get_db)):
    return {"doctors": [serialize_doctor(d).model_dump(mode="json") for d in service.all_doctors(db)]}


@router.post("/doctors", status_code=201)
def add_doctor(payload: AdminDoctorCreate, db: Session = Depends(get_db)):
    return serialize_doctor(service.add_doctor(db, payload))


@router.put("/doctors/{doctor_id}/approval")
def approval(doctor_id: str, db: Session = Depends(get_db)):
    return serialize_doctor(service.toggle_approval(db, doctor_id))


@router.put("/doctors/{doctor_id}/availability")
def availability(doctor_id: str, db: Session = Depends(get_db)):
    return serialize_doctor(service.toggle_availability(db, doctor_id))


@router.get("/appointments")
def appointments(db: Session = Depends(get_db)):
    from app.schemas import AppointmentPublic
    result = []
    for item in service.appointments(db):
        row = AppointmentPublic.model_validate(item).model_dump(mode="json")
        row["doctor"] = serialize_doctor(item.slot.doctor).model_dump(mode="json")
        row["patient_name"] = item.patient.user.full_name
        row["patient_email"] = item.patient.user.email
        row["doctor_name"] = item.slot.doctor.user.full_name
        result.append(row)
    return {"appointments": result}


@router.get("/users")
def users(db: Session = Depends(get_db)):
    from app.schemas import UserPublic
    return {"users": [UserPublic.model_validate(u).model_dump(mode="json") for u in db.query(User).order_by(User.created_at.desc()).all()]}


@router.put("/users/{user_id}/status")
def user_status(user_id: str, active: bool, db: Session = Depends(get_db)):
    from app.schemas import UserPublic
    return UserPublic.model_validate(service.set_user_active(db, user_id, active))
