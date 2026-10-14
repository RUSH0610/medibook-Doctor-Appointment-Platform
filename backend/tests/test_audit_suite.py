from datetime import datetime, timedelta, timezone
import pytest
from app.config import settings
from app.models import AppointmentStatus, AvailabilitySlot, Doctor, Patient, Role, User
from app.security import hash_password
from tests.conftest import register
from tests.test_api import create_doctor


def test_appointment_reschedule_and_conflict(client):
    doctor_id, doctor_auth = create_doctor(client)
    patient = register(client, "reschedule_patient@example.com", "Reschedule Patient")
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}

    future1 = datetime.now(timezone.utc) + timedelta(days=2)
    future2 = datetime.now(timezone.utc) + timedelta(days=3)

    slot1 = client.post("/api/v1/availability", json={
        "starts_at": future1.isoformat(),
        "ends_at": (future1 + timedelta(minutes=30)).isoformat()
    }, headers=doctor_auth).json()

    slot2 = client.post("/api/v1/availability", json={
        "starts_at": future2.isoformat(),
        "ends_at": (future2 + timedelta(minutes=30)).isoformat()
    }, headers=doctor_auth).json()

    # Book slot1
    booked = client.post("/api/v1/appointments", json={"slot_id": slot1["id"], "reason": "Initial"}, headers=patient_auth)
    assert booked.status_code == 201
    appt_id = booked.json()["id"]

    # Reschedule to slot2
    rescheduled = client.post(f"/api/v1/appointments/{appt_id}/reschedule", json={"slot_id": slot2["id"], "reason": "Moved to slot 2"}, headers=patient_auth)
    assert rescheduled.status_code == 200
    new_appt_id = rescheduled.json()["id"]
    assert rescheduled.json()["status"] == "BOOKED"
    assert rescheduled.json()["slot_id"] == slot2["id"]

    # Slot 1 is now free and can be booked again
    rebooked_slot1 = client.post("/api/v1/appointments", json={"slot_id": slot1["id"], "reason": "Rebooking slot 1"}, headers=patient_auth)
    assert rebooked_slot1.status_code == 201

    # Attempting to reschedule into slot 1 now should conflict (409)
    conflict = client.post(f"/api/v1/appointments/{new_appt_id}/reschedule", json={"slot_id": slot1["id"]}, headers=patient_auth)
    assert conflict.status_code == 409


def test_notifications_lifecycle(client):
    doctor_id, doctor_auth = create_doctor(client)
    patient = register(client, "notif_patient@example.com", "Notif Patient")
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}

    future = datetime.now(timezone.utc) + timedelta(days=5)
    slot = client.post("/api/v1/availability", json={
        "starts_at": future.isoformat(),
        "ends_at": (future + timedelta(minutes=30)).isoformat()
    }, headers=doctor_auth).json()

    # Booking generates notification for doctor
    booked = client.post("/api/v1/appointments", json={"slot_id": slot["id"]}, headers=patient_auth)
    assert booked.status_code == 201

    # Doctor checks unread count
    doctor_unread = client.get("/api/v1/notifications/unread-count", headers=doctor_auth)
    assert doctor_unread.status_code == 200
    assert doctor_unread.json()["count"] >= 1

    # Doctor lists notifications
    notifs = client.get("/api/v1/notifications/", headers=doctor_auth).json()["notifications"]
    assert len(notifs) >= 1
    notif_id = notifs[0]["id"]
    assert notifs[0]["is_read"] is False

    # Mark single notification as read
    mark_res = client.post(f"/api/v1/notifications/{notif_id}/read", headers=doctor_auth)
    assert mark_res.status_code == 200
    assert mark_res.json()["is_read"] is True

    # Mark all read
    read_all_res = client.post("/api/v1/notifications/read-all", headers=doctor_auth)
    assert read_all_res.status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=doctor_auth).json()["count"] == 0


def test_reviews_lifecycle_and_admin_toggle(client):
    doctor_id, doctor_auth = create_doctor(client)
    patient = register(client, "review_patient@example.com", "Review Patient")
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}

    future = datetime.now(timezone.utc) + timedelta(days=6)
    slot = client.post("/api/v1/availability", json={
        "starts_at": future.isoformat(),
        "ends_at": (future + timedelta(minutes=30)).isoformat()
    }, headers=doctor_auth).json()

    booked = client.post("/api/v1/appointments", json={"slot_id": slot["id"]}, headers=patient_auth)
    appt_id = booked.json()["id"]

    # Try review before completion -> 409
    rev_payload = {"appointment_id": appt_id, "rating": 5, "comment": "Great doctor!", "is_anonymous": False}
    fail_rev = client.post("/api/v1/reviews/", json=rev_payload, headers=patient_auth)
    assert fail_rev.status_code == 409

    # Set slot to past and complete appointment
    db = client.app.state.testing_session()
    stored_slot = db.get(AvailabilitySlot, slot["id"])
    stored_slot.starts_at = datetime.now(timezone.utc) - timedelta(hours=2)
    stored_slot.ends_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    db.close()

    complete_res = client.post(f"/api/v1/appointments/{appt_id}/complete", headers=doctor_auth)
    assert complete_res.status_code == 200

    # Submit review
    rev_res = client.post("/api/v1/reviews/", json=rev_payload, headers=patient_auth)
    assert rev_res.status_code == 201
    rev_id = rev_res.json()["id"]

    # Duplicate review -> 409
    dup_res = client.post("/api/v1/reviews/", json=rev_payload, headers=patient_auth)
    assert dup_res.status_code == 409

    # Doctor review listing
    doc_reviews = client.get(f"/api/v1/reviews/doctor/{doctor_id}").json()["reviews"]
    assert len(doc_reviews) == 1
    assert doc_reviews[0]["id"] == rev_id
    assert doc_reviews[0]["patientName"] == "Review Patient"

    # Admin operations on reviews
    db = client.app.state.testing_session()
    admin = User(full_name="Admin Reviewer", email="admin_rev@example.org", password_hash=hash_password("AdminPass123"), role=Role.ADMIN)
    db.add(admin)
    db.commit()
    db.close()

    admin_token = client.post("/api/v1/auth/login", json={"email": "admin_rev@example.org", "password": "AdminPass123"}).json()["access_token"]
    admin_auth = {"Authorization": f"Bearer {admin_token}"}

    all_revs = client.get("/api/v1/reviews/", headers=admin_auth).json()["reviews"]
    assert len(all_revs) >= 1

    # Toggle review approval
    toggled = client.put(f"/api/v1/reviews/{rev_id}/approval", headers=admin_auth)
    assert toggled.status_code == 200
    assert toggled.json()["isApproved"] is False

    # Doctor public review list hides unapproved reviews
    doc_reviews_hidden = client.get(f"/api/v1/reviews/doctor/{doctor_id}").json()["reviews"]
    assert len(doc_reviews_hidden) == 0


def test_medical_records_serialization_and_token_download(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))
    patient = register(client, "medrec_patient@example.com", "MedRec Patient")
    doctor_id, doctor_auth = create_doctor(client)
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}

    upload = client.post(
        "/api/v1/medical-records/",
        data={"title": "Blood Test", "record_type": "Pathology", "notes": "Fasting blood sugar 95"},
        files={"file": ("report.pdf", b"%PDF-1.4 sample content", "application/pdf")},
        headers=patient_auth
    )
    assert upload.status_code == 201
    rec = upload.json()
    assert rec["category"] == "Pathology"
    assert rec["recordType"] == "Pathology"
    assert rec["notes"] == "Fasting blood sugar 95"
    assert rec["description"] == "Fasting blood sugar 95"
    assert rec["isSharedWithDoctor"] is False
    assert rec["sharedWithDoctors"] == []
    rec_id = rec["id"]

    # Share with doctor
    share_res = client.post("/api/v1/medical-records/share", json={"recordId": rec_id, "doctorId": doctor_id}, headers=patient_auth)
    assert share_res.status_code == 200

    # Retrieve patient records list and verify shared status
    records_list = client.get("/api/v1/medical-records/", headers=patient_auth).json()["records"]
    assert len(records_list) == 1
    assert records_list[0]["isSharedWithDoctor"] is True
    assert doctor_id in records_list[0]["sharedWithDoctors"]

    # Query param token file access (direct browser download without Authorization header)
    file_via_query_token = client.get(f"/api/v1/medical-records/{rec_id}/file?token={patient['access_token']}")
    assert file_via_query_token.status_code == 200
    assert file_via_query_token.content == b"%PDF-1.4 sample content"


def test_admin_doctor_and_user_management(client):
    db = client.app.state.testing_session()
    admin = User(full_name="Admin Manager", email="admin_mgr@example.org", password_hash=hash_password("AdminPass123"), role=Role.ADMIN)
    db.add(admin)
    db.commit()
    db.close()

    admin_token = client.post("/api/v1/auth/login", json={"email": "admin_mgr@example.org", "password": "AdminPass123"}).json()["access_token"]
    admin_auth = {"Authorization": f"Bearer {admin_token}"}

    # Add a doctor via Admin API
    new_doc_payload = {
        "full_name": "Dr. Admin Added",
        "email": "dr_added@example.com",
        "password": "AddedDocPass123",
        "specialization": "Dermatology",
        "qualification": "MBBS, MD",
        "experience_years": 8,
        "consultation_fee": "650",
        "bio": "Skin specialist"
    }
    doc_res = client.post("/api/v1/admin/doctors", json=new_doc_payload, headers=admin_auth)
    assert doc_res.status_code == 201
    created_doc = doc_res.json()
    doc_id = created_doc["id"]
    assert created_doc["specialization"] == "Dermatology"

    # Toggle doctor approval (initial is False -> becomes True)
    toggle_appr = client.put(f"/api/v1/admin/doctors/{doc_id}/approval", headers=admin_auth)
    assert toggle_appr.status_code == 200
    assert toggle_appr.json()["is_approved"] is True

    # Toggle doctor availability
    toggle_avail = client.put(f"/api/v1/admin/doctors/{doc_id}/availability", headers=admin_auth)
    assert toggle_avail.status_code == 200
    assert toggle_avail.json()["is_available"] is False

    # Toggle user active status
    user_id = created_doc["user_id"]
    deactivate = client.put(f"/api/v1/admin/users/{user_id}/status?active=false", headers=admin_auth)
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    # Deactivated user cannot log in
    login_attempt = client.post("/api/v1/auth/login", json={"email": "dr_added@example.com", "password": "AddedDocPass123"})
    assert login_attempt.status_code == 401

    # Re-activate user
    activate = client.put(f"/api/v1/admin/users/{user_id}/status?active=true", headers=admin_auth)
    assert activate.status_code == 200
    assert activate.json()["is_active"] is True


def test_symptom_checker_unconfigured_error(client, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    res = client.post("/api/v1/ai/symptom-check", json={"symptoms": "Mild headache and fatigue for 2 days"})
    assert res.status_code == 503
    assert "Symptom checker is unavailable until GROQ_API_KEY is configured" in res.json()["detail"]
