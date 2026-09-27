from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.notification_models import Notification
from backend.user_models import User
from backend.services.permissions import require_admin_or_hr
from backend.routers.auth import get_current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: str = "General"


# ============================================================
# RESPONSE HELPER
# ============================================================

def serialize_notification(notification: Notification):
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }


# ============================================================
# CREATE NOTIFICATION
# Admin / HR Manager only
# ============================================================

@router.post("/")
def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    # Basic validation
    title = notification_data.title.strip()
    message = notification_data.message.strip()
    notification_type = notification_data.type.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Notification title cannot be empty",
        )

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Notification message cannot be empty",
        )

    if not notification_type:
        notification_type = "General"

    # Verify target user exists
    user = (
        db.query(User)
        .filter(
            User.id == notification_data.user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    notification = Notification(
        user_id=notification_data.user_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False,
    )

    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Notification could not be created "
                "because of a data conflict"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Notification could not be created",
        )

    return {
        "message": "Notification created successfully",
        "notification": serialize_notification(
            notification
        ),
    }


# ============================================================
# GET MY NOTIFICATIONS
# ============================================================

@router.get("/")
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id
        )
        .order_by(Notification.id.desc())
        .all()
    )

    return [
        serialize_notification(notification)
        for notification in notifications
    ]


# ============================================================
# MARK NOTIFICATION AS READ
# ============================================================

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    # Horizontal privilege protection:
    # users can only modify their own notifications.
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You can only update "
                "your own notifications"
            ),
        )

    notification.is_read = True

    try:
        db.commit()
        db.refresh(notification)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Notification could not be marked "
                "as read because of a data conflict"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Notification could not be marked as read",
        )

    return {
        "message": "Notification marked as read",
        "notification": serialize_notification(
            notification
        ),
    }


# ============================================================
# DELETE NOTIFICATION
# ============================================================

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    # Horizontal privilege protection:
    # users can only delete their own notifications.
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You can only delete "
                "your own notifications"
            ),
        )

    try:
        db.delete(notification)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Notification could not be deleted "
                "because it is referenced by another record"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Notification could not be deleted",
        )

    return {
        "message": "Notification deleted successfully",
        "notification_id": notification_id,
    }