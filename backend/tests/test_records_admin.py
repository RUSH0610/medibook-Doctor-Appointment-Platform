from app.config import settings
from app.models import Role, User
from app.security import hash_password
from tests.conftest import register
from tests.test_api import create_doctor


def test_record_upload_share_and_private_file_access(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_directory", str(tmp_path))
    patient = register(client)
    other = register(client, "other@example.org", "Other Patient")
    doctor_id, doctor_auth = create_doctor(client)
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}
    other_auth = {"Authorization": f"Bearer {other['access_token']}"}
    upload = client.post("/api/v1/medical-records/", data={"title": "Lab result", "record_type": "Lab Report"}, files={"file": ("result.pdf", b"%PDF-1.4 sample", "application/pdf")}, headers=patient_auth)
    assert upload.status_code == 201
    record_id = upload.json()["id"]
    assert client.get(f"/api/v1/medical-records/{record_id}/file", headers=patient_auth).status_code == 200
    assert client.get(f"/api/v1/medical-records/{record_id}/file", headers=other_auth).status_code == 404
    shared = client.post("/api/v1/medical-records/share", json={"recordId": record_id, "doctorId": doctor_id}, headers=patient_auth)
    assert shared.status_code == 200
    assert len(client.get("/api/v1/medical-records/shared-with-me", headers=doctor_auth).json()["records"]) == 1


def test_admin_routes_require_admin_role(client):
    patient = register(client)
    patient_auth = {"Authorization": f"Bearer {patient['access_token']}"}
    assert client.get("/api/v1/admin/dashboard", headers=patient_auth).status_code == 403
    db = client.app.state.testing_session()
    admin = User(full_name="Admin", email="admin@example.org", password_hash=hash_password("AdminPassword123"), role=Role.ADMIN)
    db.add(admin)
    db.commit()
    db.close()
    token = client.post("/api/v1/auth/login", json={"email": "admin@example.org", "password": "AdminPassword123"}).json()["access_token"]
    response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "earnings" in response.json()["dashData"]
