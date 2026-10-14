from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Patient, Role, User
from app.schemas import PatientRegister
from app.security import create_access_token, hash_password, verify_password


def register_patient(db: Session, payload: PatientRegister) -> tuple[User, str]:
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), role=Role.PATIENT, phone=payload.phone)
    user.patient = Patient(date_of_birth=payload.date_of_birth, gender=payload.gender)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    db.refresh(user)
    return user, create_access_token(user.id, user.role.value)


def authenticate(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return user, create_access_token(user.id, user.role.value)
