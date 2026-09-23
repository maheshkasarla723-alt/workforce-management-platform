from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.audit_models import AuditLog
from backend.services.permissions import require_admin


router = APIRouter(
    prefix="/api/audit-logs",
    tags=["Audit Logs"]
)


# ==================================================
# GET ALL AUDIT LOGS
# ADMIN ONLY
# ==================================================

@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .all()
    )

    result = []

    for log in logs:

        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at
        })

    return result