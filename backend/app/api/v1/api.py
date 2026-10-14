from fastapi import APIRouter
from app.api.v1.endpoints import admin, appointments, auth, availability, dashboard, doctors, medical_records, notifications, prescriptions, reviews, symptom_checker, users

api_router = APIRouter(prefix="/api/v1")
for router in (auth.router, doctors.router, availability.router, appointments.router, prescriptions.router, dashboard.router, users.router, medical_records.router, reviews.router, notifications.router, symptom_checker.router, admin.router):
    api_router.include_router(router)
