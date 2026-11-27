import json

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.db import get_db
from app.models import Notification
from app.routers.common import aware
from app.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["thông báo"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.created_at.desc()).limit(30))
    return [NotificationOut(id=n.id, kind=n.kind, payload=json.loads(n.payload or "{}"), read=n.read,
                            created_at=aware(n.created_at)) for n in rows]


@router.post("/read", status_code=204)
def mark_all_read(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(update(Notification).where(Notification.user_id == user.id, Notification.read.is_(False)).values(read=True))
    db.commit()
