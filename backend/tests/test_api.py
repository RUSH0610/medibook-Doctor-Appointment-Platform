from datetime import datetime, timedelta, timezone
import jwt
from app.models import Doctor, Role, User
from app.security import hash_password
from tests.conftest import register
from app.models import AvailabilitySlot
from app.config import settings


def create_doctor(client):
    db = client.app.state.testing_session()
    user = User(full_name="Dr. Example", email="doctor@example.com", password_hash=hash_password("DoctorPassword123"), role=Role.DOCTOR)
    db.add(user); db.flush()
    doctor = Doctor(user_id=user.id, specialization="Cardiology", qualification="MD", experience_years=7, consultation_fee="800", bio="Experienced cardiologist")
    db.add(doctor); db.commit(); doctor_id = doctor.id
    db.close()
    token = client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "DoctorPassword123"}).json()["access_token"]
    return doctor_id, {"Authorization": f"Bearer {token}"}


def test_registration_duplicate_login_and_authz(client):
    data = register(client)
    assert data["user"]["role"] == "PATIENT"
    assert "password_hash" not in data["user"]
    assert client.post("/api/v1/auth/register", json={"full_name": "Test Patient", "email": "patient@example.com", "password": "GoodPassword123"}).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email": "patient@example.com", "password": "wrong-password"}).status_code == 401
    assert client.post("/api/v1/availability", json={}, headers={"Authorization": f"Bearer {data['access_token']}"}).status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    expired = jwt.encode({"sub": data["user"]["id"], "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.jwt_secret, algorithm="HS256")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_doctor_discovery_and_slot_validation(client):
    doctor_id, auth = create_doctor(client)
    assert client.get("/api/v1/doctors?specialization=cardiology").json()[0]["id"] == doctor_id
    future = datetime.now(timezone.utc) + timedelta(days=2)
    body = {"starts_at": future.isoformat(), "ends_at": (future + timedelta(minutes=30)).isoformat()}
    assert client.post("/api/v1/availability", json=body, headers=auth).status_code == 201
    assert client.post("/api/v1/availability", json=body, headers=auth).status_code == 409
    no_timezone = {"starts_at": future.replace(tzinfo=None).isoformat(), "ends_at": (future + timedelta(minutes=30)).replace(tzinfo=None).isoformat()}
    assert client.post("/api/v1/availability", json=no_timezone, headers=auth).status_code == 422


def test_double_booking_cancel_rebook_and_ownership(client):
    doctor_id, doctor_auth = create_doctor(client)
    patient = register(client)
    other = register(client, "other@example.org", "Other Patient")
    future = datetime.now(timezone.utc) + timedelta(days=3)
    slot = client.post("/api/v1/availability", json={"starts_at": future.isoformat(), "ends_at": (future + timedelta(minutes=30)).isoformat()}, headers=doctor_auth).json()
    a = {"Authorization": f"Bearer {patient['access_token']}"}; b = {"Authorization": f"Bearer {other['access_token']}"}
    first = client.post("/api/v1/appointments", json={"slot_id": slot["id"]}, headers=a)
    assert first.status_code == 201
    assert client.get("/api/v1/appointments/me", headers=doctor_auth).json()[0]["patient_name"] == "Test Patient"
    assert client.get("/api/v1/dashboard", headers=a).json()["upcoming_count"] == 1
    assert client.post("/api/v1/appointments", json={"slot_id": slot["id"]}, headers=b).status_code == 409
    assert client.post(f"/api/v1/appointments/{first.json()['id']}/cancel", headers=b).status_code == 404
    assert client.post(f"/api/v1/appointments/{first.json()['id']}/cancel", headers=a).status_code == 200
    assert client.get("/api/v1/dashboard", headers=a).json()["appointment_counts"]["cancelled"] == 1
    assert client.post("/api/v1/appointments", json={"slot_id": slot["id"]}, headers=b).status_code == 201


def test_unauthorized_prescription_read_is_hidden(client):
    register(client)
    assert client.get("/api/v1/prescriptions/does-not-exist").status_code == 401


def test_booking_to_prescription_and_patient_ownership(client):
    doctor_id, doctor_auth = create_doctor(client)
    patient = register(client)
    another_patient = register(client, "other@example.org", "Other Patient")
    future = datetime.now(timezone.utc) + timedelta(days=4)
    slot = client.post("/api/v1/availability", json={"starts_at": future.isoformat(), "ends_at": (future + timedelta(minutes=30)).isoformat()}, headers=doctor_auth).json()
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}
    other_auth = {"Authorization": f"Bearer {another_patient['access_token']}"}
    body = {"diagnosis": "Seasonal allergy", "doctor_notes": "Reviewed", "advice": "Rest", "items": [
        {"medicine_name": "Medicine A", "dosage": "10 mg", "frequency": "Daily", "duration": "5 days", "instructions": "After food"},
        {"medicine_name": "Medicine B", "dosage": "1 tablet", "frequency": "As needed", "duration": "3 days", "instructions": ""}
    ]}
    booked = client.post("/api/v1/appointments", json={"slot_id": slot["id"], "reason": "Consultation"}, headers=patient_auth)
    appointment_id = booked.json()["id"]
    assert client.get(f"/api/v1/doctors/{doctor_id}/availability").json() == []
    assert client.post(f"/api/v1/appointments/{appointment_id}/complete", headers=doctor_auth).status_code == 409

    db = client.app.state.testing_session()
    stored_slot = db.get(AvailabilitySlot, slot["id"])
    stored_slot.starts_at = datetime.now(timezone.utc) - timedelta(hours=1)
    stored_slot.ends_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    db.commit(); db.close()

    assert client.post(f"/api/v1/appointments/{appointment_id}/prescriptions", json=body, headers=doctor_auth).status_code == 409
    assert client.post(f"/api/v1/appointments/{appointment_id}/complete", headers=doctor_auth).status_code == 200
    created = client.post(f"/api/v1/appointments/{appointment_id}/prescriptions", json=body, headers=doctor_auth)
    assert created.status_code == 201
    prescription_id = created.json()["id"]
    assert len(created.json()["items"]) == 2
    assert client.post(f"/api/v1/appointments/{appointment_id}/prescriptions", json=body, headers=doctor_auth).status_code == 409
    assert client.get("/api/v1/prescriptions/me", headers=patient_auth).json()[0]["id"] == prescription_id
    assert client.get(f"/api/v1/prescriptions/{prescription_id}", headers=other_auth).status_code == 404
    assert client.get(f"/api/v1/prescriptions/{prescription_id}", headers=doctor_auth).status_code == 200

