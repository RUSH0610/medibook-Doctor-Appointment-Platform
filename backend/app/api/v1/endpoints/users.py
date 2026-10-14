from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user, patient_user
from app.models import Patient, User
from app.schemas import PatientProfileUpdate, UserPublic
from app.services.common import get_patient

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile")
def profile(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role.value == "PATIENT":
        patient = get_patient(db, user)
        return {"user": {**UserPublic.model_validate(user).model_dump(), **{key: getattr(patient, key) for key in ("date_of_birth", "gender", "blood_group", "insurance_provider", "insurance_policy_no", "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation", "allergies", "chronic_conditions", "current_medications", "past_surgeries")}}}
    return {"user": UserPublic.model_validate(user).model_dump()}


@router.put("/profile")
def update_profile(payload: PatientProfileUpdate, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    patient = get_patient(db, user)
    changes = payload.model_dump(exclude_unset=True)
    if "full_name" in changes:
        user.full_name = changes.pop("full_name")
    if "phone" in changes:
        user.phone = changes.pop("phone")
    for key, value in changes.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(user)
    return profile(db, user)
