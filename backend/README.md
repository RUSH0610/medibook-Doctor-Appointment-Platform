# MediBook Backend

FastAPI REST API for MediBook's patient, doctor, appointment, medical-record, prescription, review, notification, symptom-guidance, and administrative workflows.

## Backend modules

- `app/api/v1/endpoints/`: route handlers organized by feature.
- `app/services/`: workflow logic, permission checks, and database operations.
- `app/models.py`: SQLAlchemy entities, relationships, and database constraints.
- `app/schemas.py`: Pydantic input and output contracts.
- `app/dependencies.py`: database session, active-user, and role dependencies.
- `app/security.py`: Argon2 password hashing and JWT access-token creation.
- `app/config.py`: environment-backed settings.
- `migrations/`: Alembic environment and versioned schema revisions.
- `scripts/seed.py`: repeatable local doctor and optional administrator setup.
- `tests/`: API-level tests using an isolated SQLite database.

## Local development

Run these commands from the `backend` directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Configure `DATABASE_URL` and a private `JWT_SECRET` in `.env`. Set `DOCTOR_PASSWORD` to a private password of at least 12 characters. Optionally configure both `ADMIN_EMAIL` and `ADMIN_PASSWORD` to seed an administrator. Create a PostgreSQL database first.

```powershell
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore endpoints. Run tests with:

```powershell
python -m pytest
```

The application uses Alembic for schema management; application startup does not create or modify the database schema. The standard test suite uses SQLite for fast API checks. PostgreSQL-specific locking behavior should be checked against PostgreSQL separately.

## API areas

All business routes are prefixed with `/api/v1`:

- Authentication and user profiles
- Doctor discovery, profiles, and availability
- Appointment booking, cancellation, rescheduling, and completion
- Patient and doctor dashboards
- Prescriptions and medicine items
- Medical records and controlled sharing
- Reviews and moderation
- In-app notifications
- Optional symptom guidance
- Administration

See [`../docs/API_REFERENCE.md`](../docs/API_REFERENCE.md) for the route overview and [`../docs/DATABASE.md`](../docs/DATABASE.md) for the entities and their relationships.

## Operational notes

Uploaded files are stored in a private local directory by default. Configure durable private storage and retention policies before deployment. The symptom-guidance endpoint requires `GROQ_API_KEY`; it returns an explicit unavailable response if the provider is not configured. Do not store actual patient data in a local demo environment.
