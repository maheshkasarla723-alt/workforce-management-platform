from fastapi import Depends, HTTPException, status

from backend.routers.auth import get_current_user
from backend.user_models import User


# ==================================================
# ADMIN ONLY
# ==================================================

def require_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# ==================================================
# ADMIN OR HR MANAGER
# ==================================================

def require_admin_or_hr(
    current_user: User = Depends(get_current_user)
):
    allowed_roles = [
        "Admin",
        "HR Manager"
    ]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or HR Manager access required"
        )

    return current_user


# ==================================================
# ANY AUTHENTICATED USER
# ==================================================

def require_authenticated_user(
    current_user: User = Depends(get_current_user)
):
    return current_user