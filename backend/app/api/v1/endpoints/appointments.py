from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user, doctor_user, patient_user
from app.models import User, Appointment, AppointmentStatus, AvailabilitySlot
from app.schemas import AppointmentCreate, AppointmentPublic, DoctorPublic
from app.services.appointments import book, cancel, complete, list_for_user, reschedule as reschedule_service
from app.services.common import get_doctor
from app.services.notifications import create as notify
from app.schemas import PrescriptionCreate
from app.services.prescriptions import create as create_prescription

router = APIRouter(prefix="/appointments", tags=["appointments"])


def with_patient_name(appt: Appointment, is_doctor: bool) -> AppointmentPublic:
    result = AppointmentPublic.model_validate(appt)
    result.doctor = DoctorPublic.model_validate({
        "id": appt.slot.doctor.id, "full_name": appt.slot.doctor.user.full_name,
        "specialization": appt.slot.doctor.specialization, "qualification": appt.slot.doctor.qualification,
        "experience_years": appt.slot.doctor.experience_years, "consultation_fee": appt.slot.doctor.consultation_fee,
        "bio": appt.slot.doctor.bio, "license_number": appt.slot.doctor.license_number,
        "is_approved": appt.slot.doctor.is_approved, "is_available": appt.slot.doctor.is_available,
        "email": appt.slot.doctor.user.email, "phone": appt.slot.doctor.user.phone, "avatar_url": appt.slot.doctor.user.avatar_url,
    })
    if is_doctor:
        result.patient_name = appt.patient.user.full_name
        result.patient_email = appt.patient.user.email
        result.patient_dob = appt.patient.date_of_birth
    return result


@router.post("", response_model=AppointmentPublic, status_code=201)
def create(payload: AppointmentCreate, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    appt = book(db, user, payload.slot_id, payload.reason, payload.appointment_type, payload.phone)
    # Persist an in-app event; no email/SMS provider is assumed.
    recipient = db.query(AvailabilitySlot).filter_by(id=appt.slot_id).first().doctor.user_id
    notify(db, recipient, "APPOINTMENT_BOOKED", "New appointment", "A patient booked an appointment on your schedule.", appt.id)
    db.commit()
    return appt


@router.get("/me", response_model=list[AppointmentPublic])
@router.get("/my", response_model=list[AppointmentPublic], include_in_schema=False)
@router.get("/doctor", response_model=list[AppointmentPublic], include_in_schema=False)
def mine(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [with_patient_name(a, user.role.value == "DOCTOR") for a in list_for_user(db, user)]


@router.get("/{appointment_id}", response_model=AppointmentPublic)
def detail(appointment_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    appt = next((a for a in list_for_user(db, user) if a.id == appointment_id), None)
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    return with_patient_name(appt, user.role.value == "DOCTOR")


@router.post("/{appointment_id}/cancel", response_model=AppointmentPublic)
def cancel_one(appointment_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    appt = cancel(db, user, appointment_id)
    doctor_user_id = appt.slot.doctor.user_id
    patient_user_id = appt.patient.user_id
    if user.id == doctor_user_id:
        notify(db, patient_user_id, "APPOINTMENT_CANCELLED", "Appointment cancelled", "Your doctor cancelled your upcoming appointment.", appt.id)
    elif user.id == patient_user_id:
        notify(db, doctor_user_id, "APPOINTMENT_CANCELLED", "Appointment cancelled", "A patient cancelled an appointment on your schedule.", appt.id)
    else:
        notify(db, patient_user_id, "APPOINTMENT_CANCELLED", "Appointment cancelled", "Your appointment was cancelled by an administrator.", appt.id)
        notify(db, doctor_user_id, "APPOINTMENT_CANCELLED", "Appointment cancelled", "An appointment on your schedule was cancelled by an administrator.", appt.id)
    db.commit()
    return with_patient_name(appt, user.role.value == "DOCTOR")


@router.post("/{appointment_id}/complete", response_model=AppointmentPublic)
def complete_one(appointment_id: str, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    appt = complete(db, get_doctor(db, user), appointment_id)
    notify(db, appt.patient.user_id, "APPOINTMENT_COMPLETED", "Appointment completed", "Your doctor marked the appointment as completed.", appt.id)
    db.commit()
    return appt


@router.post("/{appointment_id}/prescriptions", status_code=201, include_in_schema=False)
def prescribe(appointment_id: str, payload: PrescriptionCreate, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    prescription = create_prescription(db, get_doctor(db, user), appointment_id, payload)
    notify(db, prescription.appointment.patient.user_id, "PRESCRIPTION_CREATED", "Prescription available", "Your doctor added a prescription.", prescription.id)
    db.commit()
    from app.api.v1.endpoints.prescriptions import serialize_prescription
    return serialize_prescription(prescription)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentPublic)
def reschedule(appointment_id: str, payload: AppointmentCreate, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    appt = reschedule_service(db, user, appointment_id, payload.slot_id, payload.reason, payload.appointment_type, payload.phone)
    doctor_user_id = appt.slot.doctor.user_id
    notify(db, doctor_user_id, "APPOINTMENT_RESCHEDULED", "Appointment rescheduled", "A patient rescheduled an appointment on your schedule.", appt.id)
    db.commit()
    return with_patient_name(appt, False)
