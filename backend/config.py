import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "Workforce Management Platform"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).lower()

DEBUG = os.getenv(
    "DEBUG",
    "false"
).lower() in {
    "1",
    "true",
    "yes"
}


# ============================================================
# SECURITY SETTINGS
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY"
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
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


# ============================================================
# CORS
# ============================================================

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5501,http://localhost:5501"
    ).split(",")
    if origin.strip()
]


# ============================================================
# APPLICATION VALIDATION
# ============================================================

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not configured."
    )


if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY is not configured."
    )


# ============================================================
# PRODUCTION SAFETY
# ============================================================

if ENVIRONMENT == "production":

    if DEBUG:
        raise ValueError(
            "DEBUG must be false in production."
        )

    if SECRET_KEY == "change-this-secret-key":
        raise ValueError(
            "A secure SECRET_KEY is required in production."
        )