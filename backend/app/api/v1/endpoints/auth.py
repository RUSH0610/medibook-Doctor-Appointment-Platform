from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user
from app.models import User
from app.schemas import LoginInput, PatientRegister, TokenResponse, UserPublic
from app.services.auth import authenticate, register_patient

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: PatientRegister, db: Session = Depends(get_db)):
    user, token = register_patient(db, payload)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user, token = authenticate(db, str(payload.email), payload.password)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return user


@router.post("/logout")
def logout(user: User = Depends(current_user)):
    # Access tokens are stateless and expire quickly; the client discards its copy.
    return {"message": "Logged out on this device"}
