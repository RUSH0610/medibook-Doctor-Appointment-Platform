from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import admin_user, patient_user
from app.models import User
from app.schemas import ReviewCreate
from app.services.common import get_patient
from app.services.reviews import all_reviews, create, for_doctor, toggle

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/doctor/{doctor_id}")
def doctor_reviews(doctor_id: str, db: Session = Depends(get_db)):
    return {"reviews": [_serialize(r) for r in for_doctor(db, doctor_id)]}


@router.post("/", status_code=201)
def submit(payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    return create(db, get_patient(db, user), payload)


@router.get("/")
def review_list(db: Session = Depends(get_db), user: User = Depends(admin_user)):
    return {"reviews": [_serialize(r) for r in all_reviews(db)]}


@router.put("/{review_id}/approval")
def approval(review_id: str, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    return _serialize(toggle(db, review_id))


def _serialize(review):
    return {"id": review.id, "appointmentId": review.appointment_id, "doctorId": review.doctor_id, "patientId": review.patient_id, "rating": review.rating, "comment": review.comment, "isApproved": review.is_approved, "isAnonymous": review.is_anonymous, "createdAt": review.created_at, "patientName": None if review.is_anonymous else review.patient.user.full_name}
