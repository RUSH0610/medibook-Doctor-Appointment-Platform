from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, Doctor, Patient, Role, User
from app.services.common import get_doctor, get_patient


def book(db: Session, user: User, slot_id: str, reason: str = "", appointment_type: str = "in-person", phone: str | None = None) -> Appointment:
    patient = get_patient(db, user)
    slot = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id).with_for_update())
    if slot is None or not slot.is_active or slot.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(404, "Available slot not found")
    if db.scalar(select(Appointment.id).where(Appointment.slot_id == slot.id, Appointment.status == AppointmentStatus.BOOKED)):
        raise HTTPException(409, "This time slot is already booked")
    appointment = Appointment(patient_id=patient.id, slot_id=slot.id, reason=reason.strip(), appointment_type=appointment_type, patient_phone=phone, consultation_fee=slot.doctor.consultation_fee)
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This time slot is already booked")
    return db.scalar(select(Appointment).where(Appointment.id == appointment.id).options(joinedload(Appointment.slot)))


def list_for_user(db: Session, user: User) -> list[Appointment]:
    query = (
        select(Appointment)
        .join(Appointment.slot)
        .options(
            joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user),
            joinedload(Appointment.patient).joinedload(Patient.user),
        )
    )
    if user.role == Role.PATIENT:
        query = query.where(Appointment.patient_id == get_patient(db, user).id)
    elif user.role == Role.DOCTOR:
        query = query.where(AvailabilitySlot.doctor_id == get_doctor(db, user).id)
    return list(db.scalars(query.order_by(AvailabilitySlot.starts_at.desc())).unique().all())


def cancel(db: Session, user: User, appointment_id: str) -> Appointment:
    appt = db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user),
            joinedload(Appointment.patient).joinedload(Patient.user),
        )
        .with_for_update()
    )
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    allowed = (
        (user.role == Role.PATIENT and appt.patient_id == get_patient(db, user).id)
        or (user.role == Role.DOCTOR and appt.slot.doctor_id == get_doctor(db, user).id)
        or user.role == Role.ADMIN
    )
    if not allowed:
        raise HTTPException(404, "Appointment not found")
    if appt.status != AppointmentStatus.BOOKED or appt.slot.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(409, "This appointment can no longer be cancelled")
    appt.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appt)
    return appt


def reschedule(
    db: Session,
    user: User,
    appointment_id: str,
    new_slot_id: str,
    reason: str = "",
    appointment_type: str = "in-person",
    phone: str | None = None,
) -> Appointment:
    old = db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user),
            joinedload(Appointment.patient).joinedload(Patient.user),
        )
        .with_for_update()
    )
    if old is None or old.patient.user_id != user.id:
        raise HTTPException(404, "Appointment not found")
    if old.status != AppointmentStatus.BOOKED or old.slot.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(409, "Only future booked appointments can be rescheduled")
    target = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.id == new_slot_id).with_for_update())
    if target is None or not target.is_active or target.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(404, "Available slot not found")
    if db.scalar(select(Appointment.id).where(Appointment.slot_id == new_slot_id, Appointment.status == AppointmentStatus.BOOKED)):
        raise HTTPException(409, "This time slot is already booked")
    old.status = AppointmentStatus.CANCELLED
    db.flush()
    updated = Appointment(
        patient_id=old.patient_id,
        slot_id=target.id,
        reason=reason.strip() or old.reason,
        appointment_type=appointment_type,
        patient_phone=phone or old.patient_phone,
        consultation_fee=target.doctor.consultation_fee,
    )
    db.add(updated)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This time slot is already booked")
    return db.scalar(
        select(Appointment)
        .where(Appointment.id == updated.id)
        .options(
            joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user),
            joinedload(Appointment.patient).joinedload(Patient.user),
        )
    )


def complete(db: Session, doctor: Doctor, appointment_id: str) -> Appointment:
    appt = db.scalar(select(Appointment).join(Appointment.slot).where(Appointment.id == appointment_id, AvailabilitySlot.doctor_id == doctor.id).options(joinedload(Appointment.slot)).with_for_update())
    if appt is None:
        raise HTTPException(404, "Appointment not found")
    if appt.status != AppointmentStatus.BOOKED:
        raise HTTPException(409, "Only booked appointments can be completed")
    if appt.slot.starts_at > datetime.now(timezone.utc):
        raise HTTPException(409, "An appointment can be completed after its scheduled start time")
    appt.status = AppointmentStatus.COMPLETED
    db.commit()
    db.refresh(appt)
    return appt


def dashboard(db: Session, user: User) -> dict:
    now = datetime.now(timezone.utc)
    query = select(Appointment).join(Appointment.slot)
    if user.role == Role.PATIENT:
        scope = Appointment.patient_id == get_patient(db, user).id
        count_scope = lambda: select(func.count()).select_from(Appointment).where(scope)
        upcoming = db.scalar(select(func.count()).select_from(Appointment).join(Appointment.slot).where(scope, Appointment.status == AppointmentStatus.BOOKED, AvailabilitySlot.starts_at >= now)) or 0
        counts = {status.value.lower(): db.scalar(count_scope().where(Appointment.status == status)) or 0 for status in AppointmentStatus}
        query = query.where(scope)
        patient_count = 0
        earnings = 0
    elif user.role == Role.DOCTOR:
        doctor_id = get_doctor(db, user).id
        scope = AvailabilitySlot.doctor_id == doctor_id
        upcoming = db.scalar(select(func.count()).select_from(Appointment).join(Appointment.slot).where(scope, Appointment.status == AppointmentStatus.BOOKED, AvailabilitySlot.starts_at >= now)) or 0
        counts = {status.value.lower(): db.scalar(select(func.count()).select_from(Appointment).join(Appointment.slot).where(scope, Appointment.status == status)) or 0 for status in AppointmentStatus}
        query = query.where(scope)
        patient_count = db.scalar(select(func.count(func.distinct(Appointment.patient_id))).join(Appointment.slot).where(AvailabilitySlot.doctor_id == doctor_id)) or 0
        earnings = db.scalar(select(func.coalesce(func.sum(Appointment.consultation_fee), 0)).join(Appointment.slot).where(AvailabilitySlot.doctor_id == doctor_id, Appointment.status == AppointmentStatus.COMPLETED)) or 0
    else:
        upcoming = db.scalar(select(func.count()).select_from(Appointment).join(Appointment.slot).where(Appointment.status == AppointmentStatus.BOOKED, AvailabilitySlot.starts_at >= now)) or 0
        counts = {status.value.lower(): db.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == status)) or 0 for status in AppointmentStatus}
        patient_count = db.scalar(select(func.count()).select_from(Patient)) or 0
        earnings = db.scalar(select(func.coalesce(func.sum(Appointment.consultation_fee), 0)).where(Appointment.status == AppointmentStatus.COMPLETED)) or 0
    recent = list(db.scalars(query.options(joinedload(Appointment.slot).joinedload(AvailabilitySlot.doctor).joinedload(Doctor.user), joinedload(Appointment.patient).joinedload(Patient.user)).order_by(AvailabilitySlot.starts_at.desc()).limit(10)).unique().all())
    return {"upcoming_count": upcoming, "appointment_counts": counts, "recent_appointments": recent, "patient_count": patient_count or 0, "completed_earnings": earnings or 0}
