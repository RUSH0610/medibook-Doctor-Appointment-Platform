from sqlalchemy import select
from app.database import SessionLocal
from app.models import Doctor, Role, User
from app.security import hash_password
from app.config import settings


def ensure_account(db, *, email: str, password: str, name: str, role: Role) -> User:
    normalized = email.strip().lower()
    account = db.scalar(select(User).where(User.email == normalized))
    if account is None:
        account = User(full_name=name, email=normalized, password_hash=hash_password(password), role=role)
        db.add(account)
        db.flush()
    elif account.role != role:
        raise SystemExit(f"Seed email {normalized} is already assigned a different role.")
    return account


def main():
    doctor_password = settings.doctor_password.strip()
    if len(doctor_password) < 12:
        raise SystemExit("Set a private DOCTOR_PASSWORD (at least 12 characters) in backend/.env before seeding.")
    db = SessionLocal()
    try:
        doctor_email = settings.doctor_email.strip()
        doctor_user = ensure_account(db, email=doctor_email, password=doctor_password, name=settings.doctor_name, role=Role.DOCTOR)
        if db.scalar(select(Doctor.id).where(Doctor.user_id == doctor_user.id)) is None:
            db.add(Doctor(user_id=doctor_user.id, specialization=settings.doctor_specialization, qualification="MBBS", experience_years=5, consultation_fee="500.00", bio="Available for general consultations."))
        admin_email = settings.admin_email.strip()
        admin_password = settings.admin_password.strip()
        if admin_email or admin_password:
            if not admin_email or len(admin_password) < 12:
                raise SystemExit("Set both ADMIN_EMAIL and a private ADMIN_PASSWORD of at least 12 characters, or leave both empty.")
            ensure_account(db, email=admin_email, password=admin_password, name=settings.admin_name, role=Role.ADMIN)
        db.commit()
        print(f"Seed doctor ready: {doctor_email.lower()}")
        if admin_email:
            print(f"Seed administrator ready: {admin_email.lower()}")
        print("Login passwords are read only from your local .env.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
