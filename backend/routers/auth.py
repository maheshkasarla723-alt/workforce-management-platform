from datetime import datetime, timedelta
import os

from dotenv import load_dotenv

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from jose import JWTError, jwt

from passlib.context import CryptContext

from pydantic import BaseModel, EmailStr

from sqlalchemy.orm import Session

from backend.database import get_db
from backend.user_models import User


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# ============================================================
# SECURITY CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not configured in the .env file."
    )


ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)


ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
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
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def hash_password(
    password: str
) -> str:

    return pwd_context.hash(
        password
    )


# ============================================================
# JWT TOKEN HELPER
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):

    to_encode = data.copy()

    expire = (
        datetime.utcnow()
        +
        (
            expires_delta
            if expires_delta
            else timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials =
        Depends(security),

    db: Session =
        Depends(get_db)
):

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="Invalid or expired token",

        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get(
            "username"
        )

        if not username:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    if not user:

        raise credentials_exception

    return user


# ============================================================
# REGISTER
# ============================================================

@router.post("/register")
def register(
    request: RegisterRequest,

    db: Session =
        Depends(get_db)
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
            )
        )

    # --------------------------------------------------------
    # Check username
    # --------------------------------------------------------

    existing_username = (
        db.query(User)
        .filter(
            User.username ==
            request.username
        )
        .first()
    )

    if existing_username:

        raise HTTPException(
            status_code=409,

            detail=(
                "Username already registered"
            )
        )

    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    existing_email = (
        db.query(User)
        .filter(
            User.email ==
            request.email
        )
        .first()
    )

    if existing_email:

        raise HTTPException(
            status_code=409,

            detail=(
                "Email already registered"
            )
        )

    # --------------------------------------------------------
    # Password validation
    # --------------------------------------------------------

    if len(request.password) < 8:

        raise HTTPException(
            status_code=400,

            detail=(
                "Password must be at least "
                "8 characters."
            )
        )

    # --------------------------------------------------------
    # Create Employee user
    # --------------------------------------------------------

    user = User(

        username=request.username,

        email=request.email,

        hashed_password=(
            hash_password(
                request.password
            )
        ),

        role="Employee"
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return {

        "message":
            "User registered successfully",

        "user": {

            "id":
                user.id,

            "username":
                user.username,

            "email":
                user.email,

            "role":
                user.role
        }
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    request: LoginRequest,

    db: Session =
        Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.username ==
            request.username
        )
        .first()
    )

    # --------------------------------------------------------
    # Use the same generic message for invalid username
    # and invalid password.
    # --------------------------------------------------------

    if (
        not user
        or
        not verify_password(
            request.password,
            user.hashed_password
        )
    ):

        raise HTTPException(
            status_code=401,

            detail=(
                "Invalid username or password"
            )
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    token = create_access_token({

        "sub":
            str(user.id),

        "username":
            user.username,

        "role":
            user.role
    })

    return {

        "access_token":
            token,

        "token_type":
            "bearer",

        "user": {

            "id":
                user.id,

            "username":
                user.username,

            "email":
                user.email,

            "role":
                user.role
        }
    }


# ============================================================
# CURRENT USER DETAILS
# ============================================================

@router.get("/me")
def get_me(
    current_user: User =
        Depends(get_current_user)
):

    return {

        "id":
            current_user.id,

        "username":
            current_user.username,

        "email":
            current_user.email,

        "role":
            current_user.role
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,

    current_user: User =
        Depends(get_current_user),

    db: Session =
        Depends(get_db)
):

    # --------------------------------------------------------
    # New password length
    # --------------------------------------------------------

    if len(request.new_password) < 8:

        raise HTTPException(
            status_code=400,

            detail=(
                "New password must be at least "
                "8 characters."
            )
        )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        request.current_password,
        current_user.hashed_password
    ):

        raise HTTPException(
            status_code=400,

            detail=(
                "Current password is incorrect."
            )
        )

    # --------------------------------------------------------
    # New password must be different
    # --------------------------------------------------------

    if (
        request.current_password
        ==
        request.new_password
    ):

        raise HTTPException(
            status_code=400,

            detail=(
                "New password must be different "
                "from the current password."
            )
        )

    # --------------------------------------------------------
    # Hash and save new password
    # --------------------------------------------------------

    current_user.hashed_password = (
        hash_password(
            request.new_password
        )
    )

    db.commit()

    return {

        "message":
            "Password changed successfully"
    }