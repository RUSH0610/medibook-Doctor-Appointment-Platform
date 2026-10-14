from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import doctor_user
from app.models import Appointment, AppointmentStatus, AvailabilitySlot, User
from app.schemas import SlotCreate, SlotPublic
from app.services.common import get_doctor
from app.services.doctors import add_slot, available_slots, remove_slot

router = APIRouter(tags=["availability"])


@router.post("/availability", response_model=SlotPublic, status_code=201)
def create(payload: SlotCreate, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    doctor = get_doctor(db, user)
    slot = add_slot(db, doctor, payload)
    return slot


@router.get("/doctors/{doctor_id}/availability", response_model=list[SlotPublic])
def list_slots(doctor_id: str, day: date | None = Query(default=None), date_filter: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return available_slots(db, doctor_id, day or date_filter)


@router.get("/doctors/me/availability", response_model=list[SlotPublic])
def my_slots(db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    doctor = get_doctor(db, user)
    slots = list(db.query(AvailabilitySlot).filter_by(doctor_id=doctor.id, is_active=True).order_by(AvailabilitySlot.starts_at).all())
    booked = set(db.query(Appointment.slot_id).filter(Appointment.status == AppointmentStatus.BOOKED).all())
    booked = {item[0] for item in booked}
    return [{"id": slot.id, "doctor_id": slot.doctor_id, "starts_at": slot.starts_at, "ends_at": slot.ends_at, "is_active": slot.is_active, "is_booked": slot.id in booked} for slot in slots]


@router.delete("/availability/{slot_id}", status_code=204)
def deactivate(slot_id: str, db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    remove_slot(db, get_doctor(db, user), slot_id)
    return Response(status_code=204)
