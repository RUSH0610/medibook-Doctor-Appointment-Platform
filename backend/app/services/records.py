from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.models import Doctor, MedicalRecord, Patient, User, Role
from app.schemas import MedicalRecordCreate

ALLOWED = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


async def upload(db: Session, patient: Patient, meta: MedicalRecordCreate, file: UploadFile) -> MedicalRecord:
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED:
        raise HTTPException(415, "Upload a PDF, JPEG, PNG, or WebP file")
    content = await file.read(settings.max_upload_bytes + 1)
    if not content or len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "File must be non-empty and no larger than 10 MB")
    valid_signature = {
        "application/pdf": content.startswith(b"%PDF-"),
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    }[content_type]
    if not valid_signature:
        raise HTTPException(415, "File content does not match its declared type")
    suffix = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
    import uuid
    stored_name = f"{uuid.uuid4()}{suffix}"
    folder = Path(settings.upload_directory).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / stored_name).write_bytes(content)
    record = MedicalRecord(patient_id=patient.id, title=meta.title, record_type=meta.record_type, description=meta.description, stored_name=stored_name, original_name=Path(file.filename or "record").name[:255], content_type=content_type)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_patient(db: Session, patient: Patient) -> list[MedicalRecord]:
    return list(db.scalars(select(MedicalRecord).where(MedicalRecord.patient_id == patient.id).order_by(MedicalRecord.created_at.desc())).all())


def list_shared(db: Session, doctor: Doctor) -> list[MedicalRecord]:
    return list(db.scalars(select(MedicalRecord).join(MedicalRecord.patient).join(Patient.user).where(MedicalRecord.shared_with_doctor.is_(True), MedicalRecord.doctor_id == doctor.id).options(joinedload(MedicalRecord.patient).joinedload(Patient.user)).order_by(MedicalRecord.created_at.desc())).all())


def get_for_user(db: Session, record_id: str, user: User) -> MedicalRecord:
    record = db.scalar(select(MedicalRecord).where(MedicalRecord.id == record_id).options(joinedload(MedicalRecord.patient)))
    if record is None:
        raise HTTPException(404, "Medical record not found")
    if user.role == Role.PATIENT and record.patient.user_id == user.id:
        return record
    if user.role == Role.DOCTOR and record.shared_with_doctor and record.doctor_id == db.scalar(select(Doctor.id).where(Doctor.user_id == user.id)):
        return record
    if user.role == Role.ADMIN:
        return record
    raise HTTPException(404, "Medical record not found")


def delete(db: Session, patient: Patient, record_id: str) -> MedicalRecord:
    record = db.scalar(select(MedicalRecord).where(MedicalRecord.id == record_id, MedicalRecord.patient_id == patient.id))
    if record is None:
        raise HTTPException(404, "Medical record not found")
    db.delete(record)
    db.commit()
    path = Path(settings.upload_directory).resolve() / record.stored_name
    if path.parent == Path(settings.upload_directory).resolve() and path.exists():
        path.unlink()
    return record


def share_record(db: Session, patient: Patient, record_id: str, doctor_id: str) -> MedicalRecord:
    record = db.scalar(select(MedicalRecord).where(MedicalRecord.id == record_id, MedicalRecord.patient_id == patient.id))
    if record is None:
        raise HTTPException(404, "Medical record not found")
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(404, "Doctor not found")
    record.doctor_id = doctor_id
    record.shared_with_doctor = True
    db.commit()
    db.refresh(record)
    return record
