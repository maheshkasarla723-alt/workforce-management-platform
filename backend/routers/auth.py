from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

import jwt

from passlib.context import CryptContext

from pydantic import BaseModel, EmailStr

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.user_models import User
from backend.models import Employee

from backend.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


# ============================================================
# JWT AUTHENTICATION
# ============================================================

security = HTTPBearer()


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "Employee"


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============================================================
# PASSWORD HELPERS
# ============================================================

def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def hash_password(
    password: str,
) -> str:
    return pwd_context.hash(
        password,
    )


# ============================================================
# JWT TOKEN HELPER
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
):
    to_encode = data.copy()

    expire = (
        datetime.utcnow()
        + (
            expires_delta
            if expires_delta
            else timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update({
        "exp": expire,
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get("username")
        token_version = payload.get("token_version")

        if not username:
            raise credentials_exception

        if token_version is None:
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.username == username,
        )
        .first()
    )

    if not user:
        raise credentials_exception

    # --------------------------------------------------------
    # TOKEN VERSION VALIDATION
    # --------------------------------------------------------
    # When a password is changed, token_version is increased.
    # This automatically invalidates all previously issued JWTs.
    # --------------------------------------------------------

    if token_version != user.token_version:
        raise credentials_exception

    return user


# ============================================================
# REGISTER
# ============================================================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Public registration is Employee only.
    # Admin and HR Manager accounts must be created/managed
    # by authorized administrators.
    # --------------------------------------------------------

    if request.role != "Employee":
        raise HTTPException(
            status_code=403,
            detail=(
                "Public registration is only "
                "available for Employee accounts."
            ),
        )

    # --------------------------------------------------------
    # Validate username
    # --------------------------------------------------------

    username = request.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required",
        )

    # --------------------------------------------------------
    # Check username
    # --------------------------------------------------------

    existing_username = (
        db.query(User)
        .filter(
            User.username == username,
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already registered",
        )

    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    existing_email = (
        db.query(User)
        .filter(
            User.email == request.email,
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    # --------------------------------------------------------
    # Password validation
    # --------------------------------------------------------

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    # --------------------------------------------------------
    # Create Employee user
    # --------------------------------------------------------

    user = User(
        username=username,
        email=request.email,
        hashed_password=hash_password(
            request.password,
        ),
        role="Employee",
        token_version=0,
    )

    # --------------------------------------------------------
    # Database transaction
    # --------------------------------------------------------

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Username or email is already registered",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="User could not be registered",
        )

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.username == request.username,
        )
        .first()
    )

    # --------------------------------------------------------
    # Use the same generic message for invalid username
    # and invalid password.
    # --------------------------------------------------------

    if (
        not user
        or not verify_password(
            request.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------
    # token_version is included so that password changes
    # can invalidate previously issued tokens.
    # --------------------------------------------------------

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "token_version": user.token_version,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


# ============================================================
# CURRENT USER DETAILS
# ============================================================

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee_profile = None

    # Employee users can view only their own employee/payroll information.
    # The existing employee email is used to associate the login account
    # with the employee record; no new database column is required.
    if current_user.role == "Employee":
        employee = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.email == current_user.email)
            .first()
        )

        if employee:
            profile_metadata = employee.profile_metadata or {}

            payslips = profile_metadata.get("payslips", [])
            if not isinstance(payslips, list):
                payslips = []

            employee_profile = {
                "job_role": profile_metadata.get("job_role"),
                "department": (
                    employee.department.name
                    if employee.department
                    else None
                ),
                "salary": employee.salary,
                "payslips": payslips,
            }

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "employee_profile": employee_profile,
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # New password length
    # --------------------------------------------------------

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters.",
        )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        request.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    # --------------------------------------------------------
    # New password must be different
    # --------------------------------------------------------

    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=400,
            detail=(
                "New password must be different "
                "from the current password."
            ),
        )

    # --------------------------------------------------------
    # Hash and save new password
    # --------------------------------------------------------

    current_user.hashed_password = hash_password(
        request.new_password,
    )

    # --------------------------------------------------------
    # Invalidate all previously issued JWTs
    # --------------------------------------------------------

    current_user.token_version += 1

    # --------------------------------------------------------
    # Database transaction
    # --------------------------------------------------------

    try:
        db.commit()
        db.refresh(current_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Password could not be changed",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Password could not be changed",
        )

    return {
        "message": "Password changed successfully",
    }