import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User, Role

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    token: str | None = None,
    db: Session = Depends(get_db),
) -> User:
    raw_token = credentials.credentials if credentials else token
    if not raw_token:
        raise HTTPException(401, "Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(raw_token, settings.jwt_secret, algorithms=["HS256"])
        user_id = claims.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Access token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid access token")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(401, "Account is unavailable")
    return user


def require_role(role: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, "This account does not have permission for this action")
        return user
    return dependency


patient_user = require_role(Role.PATIENT)
doctor_user = require_role(Role.DOCTOR)
admin_user = require_role(Role.ADMIN)
