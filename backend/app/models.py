import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, Uuid, func, text
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class UTCDateTime(TypeDecorator):
    """Store aware instants in UTC; restore UTC tzinfo for SQLite test runs."""
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=dialect.name != "sqlite"))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime must be timezone-aware")
        value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class Role(str, enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class AppointmentStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    patient: Mapped["Patient | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor: Mapped["Doctor | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(40))
    blood_group: Mapped[str | None] = mapped_column(String(10))
    insurance_provider: Mapped[str | None] = mapped_column(String(180))
    insurance_policy_no: Mapped[str | None] = mapped_column(String(120))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(120))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(40))
    emergency_contact_relation: Mapped[str | None] = mapped_column(String(80))
    allergies: Mapped[str] = mapped_column(Text, nullable=False, default="")
    chronic_conditions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    current_medications: Mapped[str] = mapped_column(Text, nullable=False, default="")
    past_surgeries: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    user: Mapped[User] = relationship(back_populates="patient")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = (CheckConstraint("experience_years >= 0", name="ck_doctor_experience_nonnegative"), CheckConstraint("consultation_fee >= 0", name="ck_doctor_fee_nonnegative"))
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    qualification: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    experience_years: Mapped[int] = mapped_column(nullable=False, default=0)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    license_number: Mapped[str | None] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hospital_affiliation: Mapped[str | None] = mapped_column(String(255))
    consultation_room: Mapped[str | None] = mapped_column(String(100))
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    user: Mapped[User] = relationship(back_populates="doctor")
    slots: Mapped[list["AvailabilitySlot"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = (CheckConstraint("starts_at < ends_at", name="ck_slot_order"), Index("ix_slot_doctor_start", "doctor_id", "starts_at"))
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    doctor_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    doctor: Mapped[Doctor] = relationship(back_populates="slots")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (Index("uq_booked_slot", "slot_id", unique=True, postgresql_where=text("status = 'BOOKED'"), sqlite_where=text("status = 'BOOKED'")),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("availability_slots.id", ondelete="RESTRICT"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    appointment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="in-person")
    patient_phone: Mapped[str | None] = mapped_column(String(40))
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus, name="appointment_status"), nullable=False, default=AppointmentStatus.BOOKED, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    patient: Mapped[Patient] = relationship(back_populates="appointments")
    slot: Mapped[AvailabilitySlot] = relationship(back_populates="appointments")
    prescription: Mapped["Prescription | None"] = relationship(back_populates="appointment", uselist=False)


class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = (UniqueConstraint("appointment_id", name="uq_prescription_appointment"),)
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    appointment_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    doctor_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    advice: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lab_tests: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_visit_in: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    is_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    appointment: Mapped[Appointment] = relationship(back_populates="prescription")
    items: Mapped[list["PrescriptionItem"]] = relationship(back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    prescription_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name: Mapped[str] = mapped_column(String(160), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prescription: Mapped[Prescription] = relationship(back_populates="items")


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("doctors.id", ondelete="SET NULL"))
    appointment_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("appointments.id", ondelete="SET NULL"))
    record_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    shared_with_doctor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    patient: Mapped[Patient] = relationship()


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"), UniqueConstraint("appointment_id", name="uq_review_appointment"))
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    appointment_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    appointment: Mapped[Appointment] = relationship()
    patient: Mapped[Patient] = relationship()
    doctor: Mapped[Doctor] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), nullable=False)
    user: Mapped[User] = relationship(back_populates="notifications")
