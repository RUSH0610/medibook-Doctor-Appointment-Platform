from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, Doctor, Patient, Role, User
from app.schemas import AdminDoctorCreate
from app.security import hash_password


def summary(db: Session) -> dict:
    return {
        "doctors": db.scalar(select(func.count()).select_from(Doctor)) or 0,
        "patients": db.scalar(select(func.count()).select_from(Patient)) or 0,
        "appointments": db.scalar(select(func.count()).select_from(Appointment)) or 0,
        "completed_appointments": db.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == AppointmentStatus.COMPLETED)) or 0,
        "earnings": float(db.scalar(select(func.coalesce(func.sum(Appointment.consultation_fee), 0)).where(Appointment.status == AppointmentStatus.COMPLETED)) or 0),
    }


def all_doctors(db: Session) -> list[Doctor]:
    return list(db.scalars(select(Doctor).options(joinedload(Doctor.user)).order_by(Doctor.created_at.desc())).unique().all())


def add_doctor(db: Session, payload: AdminDoctorCreate) -> Doctor:
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(409, "Email is already in use")
    user = User(full_name=payload.full_name, email=email, password_hash=hash_password(payload.password), role=Role.DOCTOR, phone=payload.phone)
    doctor = Doctor(user=user, specialization=payload.specialization, qualification=payload.qualification, experience_years=payload.experience_years, consultation_fee=payload.consultation_fee, bio=payload.bio, license_number=payload.license_number, is_approved=False)
    db.add(doctor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email is already in use")
    return db.scalar(select(Doctor).where(Doctor.id == doctor.id).options(joinedload(Doctor.user)))


def toggle_approval(db: Session, doctor_id: str) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id).options(joinedload(Doctor.user)))
    if doctor is None:
        raise HTTPException(404, "Doctor not found")
    doctor.is_approved = not doctor.is_approved
    db.commit()
    db.refresh(doctor)
    return doctor


def toggle_availability(db: Session, doctor_id: str) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id).options(joinedload(Doctor.user)))
    if doctor is None:
        raise HTTPException(404, "Doctor not found")
    doctor.is_available = not doctor.is_available
    db.commit()
    db.refresh(doctor)
    return doctor


def set_user_active(db: Session, user_id: str, active: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    user.is_active = active
    db.commit()
    return user


def appointments(db: Session) -> list[Appointment]:
    return list(db.scalars(select(Appointment).options(joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user), joinedload(Appointment.patient).joinedload(Patient.user)).order_by(Appointment.created_at.desc())).unique().all())
