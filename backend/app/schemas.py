from datetime import date, datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import AppointmentStatus, Role


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: Role
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class PatientRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=40)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=40)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class DoctorUpdate(BaseModel):
    specialization: str | None = Field(default=None, min_length=2, max_length=100)
    qualification: str | None = Field(default=None, max_length=160)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    consultation_fee: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    bio: str | None = Field(default=None, max_length=4000)
    license_number: str | None = Field(default=None, max_length=100)
    is_available: bool | None = None
    hospital_affiliation: str | None = Field(default=None, max_length=255)
    consultation_room: str | None = Field(default=None, max_length=100)


class DoctorPublic(BaseModel):
    id: str
    full_name: str
    specialization: str
    qualification: str
    experience_years: int
    consultation_fee: Decimal
    bio: str
    license_number: str | None = None
    is_approved: bool = True
    is_available: bool = True
    hospital_affiliation: str | None = None
    consultation_room: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None
    user_id: str | None = None


class SlotCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include a timezone offset")
        return value.astimezone(timezone.utc)


class SlotPublic(BaseModel):
    id: str
    doctor_id: str
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    slot_id: str
    reason: str = Field(default="", max_length=2000)
    appointment_type: str = Field(default="in-person", pattern="^(in-person|video|phone)$")
    phone: str | None = Field(default=None, max_length=40)


class AppointmentPublic(BaseModel):
    id: str
    patient_id: str
    slot_id: str
    reason: str
    status: AppointmentStatus
    slot: SlotPublic
    patient_name: str | None = None
    patient_email: EmailStr | None = None
    patient_dob: date | None = None
    doctor: DoctorPublic | None = None
    model_config = ConfigDict(from_attributes=True)


class MedicineItemInput(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=160)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    duration: str = Field(min_length=1, max_length=100)
    instructions: str = Field(default="", max_length=2000)
    quantity: int = Field(default=1, ge=1, le=1000)


class PrescriptionCreate(BaseModel):
    diagnosis: str = Field(min_length=1, max_length=4000)
    doctor_notes: str = Field(default="", max_length=4000)
    advice: str = Field(default="", max_length=4000)
    follow_up_date: date | None = None
    lab_tests: str = Field(default="", max_length=2000)
    next_visit_in: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=4000)
    items: list[MedicineItemInput] = Field(min_length=1, max_length=30)


class PrescriptionPublic(BaseModel):
    id: str
    appointment_id: str
    diagnosis: str
    doctor_notes: str
    advice: str
    follow_up_date: date | None
    lab_tests: str = ""
    next_visit_in: str = ""
    notes: str = ""
    items: list[MedicineItemInput]
    model_config = ConfigDict(from_attributes=True)


class PatientProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=40)
    blood_group: str | None = Field(default=None, max_length=10)
    insurance_provider: str | None = Field(default=None, max_length=180)
    insurance_policy_no: str | None = Field(default=None, max_length=120)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, max_length=40)
    emergency_contact_relation: str | None = Field(default=None, max_length=80)
    allergies: str | None = Field(default=None, max_length=2000)
    chronic_conditions: str | None = Field(default=None, max_length=2000)
    current_medications: str | None = Field(default=None, max_length=2000)
    past_surgeries: str | None = Field(default=None, max_length=2000)


class AdminDoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    phone: str | None = Field(default=None, max_length=40)
    specialization: str = Field(min_length=2, max_length=100)
    qualification: str = Field(max_length=160)
    experience_years: int = Field(ge=0, le=80)
    consultation_fee: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    bio: str = Field(default="", max_length=4000)
    license_number: str | None = Field(default=None, max_length=100)


class MedicalRecordCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    record_type: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=2000)


class ReviewCreate(BaseModel):
    appointment_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)
    is_anonymous: bool = False
