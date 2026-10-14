from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import current_user
from app.models import User
from app.services.notifications import list_for_user, mark_all_read, mark_read, unread_count

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
def mine(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return {"notifications": list_for_user(db, user.id)}


@router.get("/unread-count")
def unread(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return {"count": unread_count(db, user.id)}


@router.post("/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(current_user)):
    mark_all_read(db, user.id)
    return {"message": "Notifications marked as read"}


@router.post("/{notification_id}/read")
def read_one(notification_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return mark_read(db, user.id, notification_id)
