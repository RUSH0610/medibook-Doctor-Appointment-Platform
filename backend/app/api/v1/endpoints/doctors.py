from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import doctor_user
from app.models import Doctor, User
from app.schemas import DoctorPublic, DoctorUpdate
from app.services.common import get_doctor
from app.services.doctors import public_doctor, public_doctors, update_doctor as update_service

router = APIRouter(prefix="/doctors", tags=["doctors"])


def serialize(doctor: Doctor) -> DoctorPublic:
    return DoctorPublic(id=doctor.id, user_id=doctor.user_id, full_name=doctor.user.full_name, specialization=doctor.specialization, qualification=doctor.qualification, experience_years=doctor.experience_years, consultation_fee=doctor.consultation_fee, bio=doctor.bio, license_number=doctor.license_number, is_approved=doctor.is_approved, is_available=doctor.is_available, hospital_affiliation=doctor.hospital_affiliation, consultation_room=doctor.consultation_room, email=doctor.user.email, phone=doctor.user.phone, avatar_url=doctor.user.avatar_url)


@router.get("/specializations")
def specializations(db: Session = Depends(get_db)):
    return {"specializations": list(db.scalars(select(Doctor.specialization).where(Doctor.is_approved.is_(True), Doctor.is_available.is_(True)).distinct().order_by(Doctor.specialization)).all())}


@router.get("/", response_model=list[DoctorPublic])
def list_doctors(specialization: str | None = None, search: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    return [serialize(d) for d in public_doctors(db, specialization, search, offset, limit)]


@router.get("/me/profile", response_model=DoctorPublic)
def my_profile(db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    doctor = db.query(Doctor).options(joinedload(Doctor.user)).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(404, "Doctor profile not found")
    return serialize(doctor)


@router.put("/me/profile", response_model=DoctorPublic)
@router.patch("/me", response_model=DoctorPublic)
def update_profile(payload: DoctorUpdate, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    doctor = get_doctor(db, user)
    update_service(db, doctor, payload)
    db.refresh(doctor)
    return serialize(doctor)


@router.get("/{doctor_id}", response_model=DoctorPublic)
def doctor_detail(doctor_id: str, db: Session = Depends(get_db)):
    return serialize(public_doctor(db, doctor_id))
