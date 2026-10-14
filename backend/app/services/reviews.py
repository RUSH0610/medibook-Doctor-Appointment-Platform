from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, Doctor, Patient, Review, User
from app.schemas import ReviewCreate


def create(db: Session, patient: Patient, payload: ReviewCreate) -> Review:
    appt = db.scalar(select(Appointment).join(Appointment.slot).where(Appointment.id == payload.appointment_id, Appointment.patient_id == patient.id).options(joinedload(Appointment.slot)))
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    if appt.status != AppointmentStatus.COMPLETED:
        raise HTTPException(409, "You can review a doctor after a completed appointment")
    review = Review(appointment_id=appt.id, patient_id=patient.id, doctor_id=appt.slot.doctor_id, rating=payload.rating, comment=payload.comment, is_anonymous=payload.is_anonymous, is_approved=True)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A review already exists for this appointment")
    return review


def for_doctor(db: Session, doctor_id: str) -> list[Review]:
    return list(db.scalars(select(Review).where(Review.doctor_id == doctor_id, Review.is_approved.is_(True)).options(joinedload(Review.patient).joinedload(Patient.user)).order_by(Review.created_at.desc())).unique().all())


def all_reviews(db: Session) -> list[Review]:
    return list(db.scalars(select(Review).options(joinedload(Review.patient).joinedload(Patient.user), joinedload(Review.doctor)).order_by(Review.created_at.desc())).unique().all())


def toggle(db: Session, review_id: str) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(404, "Review not found")
    review.is_approved = not review.is_approved
    db.commit()
    db.refresh(review)
    return review
