from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Doctor, Patient, User


def get_patient(db: Session, user: User) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.user_id == user.id))
    if patient is None:
        raise HTTPException(404, "Patient profile not found")
    return patient


def get_doctor(db: Session, user: User) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    if doctor is None:
        raise HTTPException(404, "Doctor profile not found")
    return doctor
