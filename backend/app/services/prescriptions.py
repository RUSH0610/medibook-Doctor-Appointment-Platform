from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, Doctor, Prescription, PrescriptionItem, User, Role, Patient
from app.schemas import PrescriptionCreate


def create(db: Session, doctor: Doctor, appointment_id: str, payload: PrescriptionCreate) -> Prescription:
    appt = db.scalar(select(Appointment).join(Appointment.slot).where(Appointment.id == appointment_id, AvailabilitySlot.doctor_id == doctor.id).options(joinedload(Appointment.slot)).with_for_update())
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    if appt.status != AppointmentStatus.COMPLETED:
        raise HTTPException(409, "Prescriptions can be created only for completed appointments")
    prescription = Prescription(appointment_id=appt.id, diagnosis=payload.diagnosis, doctor_notes=payload.doctor_notes, advice=payload.advice, follow_up_date=payload.follow_up_date, lab_tests=payload.lab_tests, next_visit_in=payload.next_visit_in, notes=payload.notes, items=[PrescriptionItem(**item.model_dump()) for item in payload.items])
    db.add(prescription)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A prescription already exists for this appointment")
    return db.scalar(select(Prescription).where(Prescription.id == prescription.id).options(selectinload(Prescription.items)))


def for_patient(db: Session, patient: Patient) -> list[Prescription]:
    return list(db.scalars(select(Prescription).join(Prescription.appointment).where(Appointment.patient_id == patient.id).options(selectinload(Prescription.items), joinedload(Prescription.appointment).joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user)).order_by(Prescription.created_at.desc())).unique().all())


def for_doctor(db: Session, doctor: Doctor) -> list[Prescription]:
    return list(db.scalars(select(Prescription).join(Prescription.appointment).join(Appointment.slot).where(AvailabilitySlot.doctor_id == doctor.id).options(selectinload(Prescription.items), joinedload(Prescription.appointment).joinedload(Appointment.patient).joinedload(Patient.user)).order_by(Prescription.created_at.desc())).unique().all())


def get_for_user(db: Session, prescription_id: str, user: User) -> Prescription:
    p = db.scalar(select(Prescription).where(Prescription.id == prescription_id).options(selectinload(Prescription.items), joinedload(Prescription.appointment).joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor), joinedload(Prescription.appointment).joinedload(Appointment.patient)))
    if p is None:
        raise HTTPException(404, "Prescription not found")
    allowed = user.role == Role.ADMIN or (user.role == Role.PATIENT and p.appointment.patient.user_id == user.id) or (user.role == Role.DOCTOR and p.appointment.slot.doctor.user_id == user.id)
    if not allowed:
        raise HTTPException(404, "Prescription not found")
    return p
