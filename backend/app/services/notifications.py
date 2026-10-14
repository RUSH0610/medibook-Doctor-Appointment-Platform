from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from app.models import Notification


def create(db: Session, user_id: str, kind: str, title: str, message: str, related_id: str | None = None) -> None:
    db.add(Notification(user_id=user_id, kind=kind, title=title, message=message, related_id=related_id))


def list_for_user(db: Session, user_id: str) -> list[Notification]:
    return list(db.scalars(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(100)).all())


def unread_count(db: Session, user_id: str) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))) or 0


def mark_read(db: Session, user_id: str, notification_id: str) -> Notification:
    item = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id))
    if item is None:
        raise HTTPException(404, "Notification not found")
    item.is_read = True
    db.commit()
    return item


def mark_all_read(db: Session, user_id: str) -> None:
    db.execute(update(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False)).values(is_read=True))
    db.commit()
