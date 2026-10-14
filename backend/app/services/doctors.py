from datetime import date, datetime, time, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, Doctor, User
from app.schemas import DoctorUpdate, SlotCreate


def public_doctors(db: Session, specialization: str | None = None, search: str | None = None, offset: int = 0, limit: int = 50) -> list[Doctor]:
    query = select(Doctor).join(Doctor.user).where(Doctor.is_approved.is_(True), Doctor.is_available.is_(True), User.is_active.is_(True)).options(joinedload(Doctor.user)).order_by(Doctor.specialization, User.full_name)
    if specialization:
        query = query.where(func.lower(Doctor.specialization) == specialization.strip().lower())
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(func.lower(User.full_name).like(term) | func.lower(Doctor.specialization).like(term))
    return list(db.scalars(query.offset(offset).limit(limit)).unique().all())


def public_doctor(db: Session, doctor_id: str) -> Doctor:
    doctor = db.scalar(select(Doctor).join(Doctor.user).where(Doctor.id == doctor_id, Doctor.is_approved.is_(True), Doctor.is_available.is_(True), User.is_active.is_(True)).options(joinedload(Doctor.user)))
    if doctor is None:
        raise HTTPException(404, "Doctor not found")
    return doctor


def update_doctor(db: Session, doctor: Doctor, changes: DoctorUpdate) -> Doctor:
    values = changes.model_dump(exclude_unset=True)
    if any(value is None for value in values.values()):
        raise HTTPException(422, "Profile fields cannot be set to null")
    for key, value in values.items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor


def add_slot(db: Session, doctor: Doctor, payload: SlotCreate) -> AvailabilitySlot:
    starts, ends = payload.starts_at, payload.ends_at
    if starts >= ends or starts <= datetime.now(timezone.utc):
        raise HTTPException(422, "Availability must be a future time range with starts_at before ends_at")
    # This row lock serializes overlapping-slot checks for one doctor on PostgreSQL.
    db.scalar(select(Doctor.id).where(Doctor.id == doctor.id).with_for_update())
    conflict = db.scalar(select(AvailabilitySlot.id).where(AvailabilitySlot.doctor_id == doctor.id, AvailabilitySlot.is_active.is_(True), AvailabilitySlot.starts_at < ends, AvailabilitySlot.ends_at > starts).limit(1))
    if conflict:
        raise HTTPException(409, "This slot overlaps existing availability")
    slot = AvailabilitySlot(doctor_id=doctor.id, starts_at=starts, ends_at=ends)
    db.add(slot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Conflicting availability slot")
    db.refresh(slot)
    return slot


def available_slots(db: Session, doctor_id: str, day: date | None = None) -> list[AvailabilitySlot]:
    query = select(AvailabilitySlot).where(AvailabilitySlot.doctor_id == doctor_id, AvailabilitySlot.is_active.is_(True), AvailabilitySlot.starts_at > datetime.now(timezone.utc), ~select(Appointment.id).where(Appointment.slot_id == AvailabilitySlot.id, Appointment.status == AppointmentStatus.BOOKED).exists()).order_by(AvailabilitySlot.starts_at)
    if day:
        start = datetime.combine(day, time.min, tzinfo=timezone.utc) - timedelta(hours=14)
        end = datetime.combine(day, time.max, tzinfo=timezone.utc) + timedelta(hours=14)
        query = query.where(AvailabilitySlot.starts_at >= start, AvailabilitySlot.starts_at <= end)
    return list(db.scalars(query).all())


def remove_slot(db: Session, doctor: Doctor, slot_id: str) -> None:
    slot = db.get(AvailabilitySlot, slot_id)
    if slot is None or slot.doctor_id != doctor.id:
        raise HTTPException(404, "Slot not found")
    if db.scalar(select(Appointment.id).where(Appointment.slot_id == slot.id, Appointment.status == AppointmentStatus.BOOKED)):
        raise HTTPException(409, "A booked slot cannot be deactivated")
    slot.is_active = False
    db.commit()
