from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user, doctor_user, patient_user
from app.models import User
from app.schemas import PrescriptionCreate
from app.services.common import get_doctor, get_patient
from app.services.prescriptions import create, for_doctor, for_patient, get_for_user
from app.services.notifications import create as notify

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("/", status_code=201)
def create_from_appointment(payload: PrescriptionCreate, appointment_id: str, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    prescription = create(db, get_doctor(db, user), appointment_id, payload)
    appt = prescription.appointment
    notify(db, appt.patient.user_id, "PRESCRIPTION_CREATED", "Prescription available", "Your doctor added a prescription to your completed appointment.", prescription.id)
    db.commit()
    return _serialize(prescription)


@router.get("/my")
@router.get("/me", include_in_schema=False)
def patient_list(db: Session = Depends(get_db), user: User = Depends(patient_user)):
    return [_serialize(p) for p in for_patient(db, get_patient(db, user))]


@router.get("/doctor")
def doctor_list(db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    return [_serialize(p) for p in for_doctor(db, get_doctor(db, user))]


@router.get("/{prescription_id}")
def detail(prescription_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _serialize(get_for_user(db, prescription_id, user))


def serialize_prescription(prescription):
    appt = prescription.appointment
    doctor = appt.slot.doctor
    patient = appt.patient
    return {
        "id": prescription.id, "appointment_id": prescription.appointment_id,
        "diagnosis": prescription.diagnosis, "doctor_notes": prescription.doctor_notes,
        "advice": prescription.advice, "follow_up_date": prescription.follow_up_date,
        "lab_tests": prescription.lab_tests, "next_visit_in": prescription.next_visit_in,
        "notes": prescription.notes, "created_at": prescription.created_at,
        "doctor_name": doctor.user.full_name, "doctor_speciality": doctor.specialization,
        "patient_name": patient.user.full_name,
        "items": [{"id": item.id, "medicine_name": item.medicine_name, "dosage": item.dosage, "frequency": item.frequency, "duration": item.duration, "instructions": item.instructions, "quantity": item.quantity} for item in prescription.items],
    }


_serialize = serialize_prescription
