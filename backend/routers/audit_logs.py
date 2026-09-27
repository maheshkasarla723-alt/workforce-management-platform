from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.audit_models import AuditLog
from backend.services.permissions import require_admin


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/audit-logs",
    tags=["Audit Logs"],
)


# ============================================================
# GET AUDIT LOGS
# ADMIN ONLY
# ============================================================

@router.get("/")
def get_audit_logs(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of audit logs to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of audit logs to skip",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Return audit logs for administrators.

    Features:
    - Admin-only access
    - Pagination
    - Newest logs first
    - Safe database error handling
    - No unbounded database query
    """

    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []

        for log in logs:
            result.append(
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "entity": log.entity,
                    "entity_id": log.entity_id,
                    "details": log.details,
                    "created_at": log.created_at,
                }
            )

        return result

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve audit logs",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve audit logs",
        )