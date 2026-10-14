from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.dependencies import current_user, doctor_user, patient_user
from app.models import User
from app.schemas import MedicalRecordCreate
from app.services.common import get_doctor, get_patient
from app.services.records import delete, get_for_user, list_patient, list_shared, share_record, upload

router = APIRouter(prefix="/medical-records", tags=["medical records"])


@router.post("/", status_code=201)
async def upload_record(
    title: str = Form(...),
    record_type: str = Form(""),
    category: str = Form(""),
    description: str = Form(""),
    notes: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(patient_user),
):
    resolved_type = (record_type or category or "Other").strip()
    resolved_desc = (description or notes).strip()
    return _serialize(
        await upload(
            db,
            get_patient(db, user),
            MedicalRecordCreate(title=title, record_type=resolved_type, description=resolved_desc),
            file,
        )
    )


@router.get("/")
@router.get("/my")
def mine(db: Session = Depends(get_db), user: User = Depends(patient_user)):
    return {"records": [_serialize(r) for r in list_patient(db, get_patient(db, user))]}


@router.get("/timeline")
def timeline(db: Session = Depends(get_db), user: User = Depends(patient_user)):
    return {"records": [_serialize(r) for r in list_patient(db, get_patient(db, user))]}


@router.post("/share")
def share(payload: dict, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    if not isinstance(payload.get("recordId"), str) or not isinstance(payload.get("doctorId"), str):
        raise HTTPException(422, "recordId and doctorId are required")
    return _serialize(share_record(db, get_patient(db, user), payload["recordId"], payload["doctorId"]))


@router.get("/shared-with-me")
def shared(db: Session = Depends(get_db), user: User = Depends(doctor_user)):
    return {"records": [_serialize(r, r.patient.user.full_name) for r in list_shared(db, get_doctor(db, user))]}


@router.get("/{record_id}/file")
def file(record_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = get_for_user(db, record_id, user)
    root = Path(settings.upload_directory).resolve()
    path = (root / record.stored_name).resolve()
    if path.parent != root or not path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type=record.content_type, filename=record.original_name)


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: str, db: Session = Depends(get_db), user: User = Depends(patient_user)):
    delete(db, get_patient(db, user), record_id)


def _serialize(record, patient_name=None):
    return {
        "id": record.id,
        "title": record.title,
        "recordType": record.record_type,
        "category": record.record_type,
        "description": record.description,
        "notes": record.description,
        "fileName": record.original_name,
        "fileType": record.content_type,
        "isSharedWithDoctor": record.shared_with_doctor,
        "sharedWithDoctors": [record.doctor_id] if record.shared_with_doctor and record.doctor_id else [],
        "createdAt": record.created_at,
        "patientName": patient_name,
        "fileUrl": f"/api/v1/medical-records/{record.id}/file",
    }
