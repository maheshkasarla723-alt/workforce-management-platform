import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# BOOLEAN HELPER
# ============================================================

def get_bool(
    value: str | None,
    default: bool = False
) -> bool:

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# ============================================================
# ENVIRONMENT
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development",
).strip().lower()


# ============================================================
# DEBUG
# ============================================================

# Debug is disabled by default.
#
# Production should always use:
#
# DEBUG=false
#
DEBUG = get_bool(
    os.getenv("DEBUG"),
    default=False,
)


# ============================================================
# SECRET KEY
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

if not SECRET_KEY:

    raise RuntimeError(
        "SECRET_KEY is not configured."
    )


# Prevent accidentally using a known development value
# in production.

if (
    ENVIRONMENT == "production"
    and SECRET_KEY.lower()
    in {
        "secret",
        "changeme",
        "your-secret-key",
        "change-me",
    }
):

    raise RuntimeError(
        "A strong SECRET_KEY is required in production."
    )


# ============================================================
# JWT CONFIGURATION
# ============================================================

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256",
).strip()


ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:

    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
    )


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]


# Never allow wildcard CORS in production.

if (
    ENVIRONMENT == "production"
    and "*" in ALLOWED_ORIGINS
):

    raise RuntimeError(
        "Wildcard CORS (*) is not allowed in production."
    )


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# Never allow wildcard hosts in production.

if (
    ENVIRONMENT == "production"
    and "*" in ALLOWED_HOSTS
):

    raise RuntimeError(
        "Wildcard ALLOWED_HOSTS (*) is not allowed in production."
    )


# ============================================================
# SECURITY SETTINGS
# ============================================================

SECURE_COOKIES = ENVIRONMENT == "production"

SECURE_HEADERS_ENABLED = get_bool(
    os.getenv("SECURE_HEADERS_ENABLED"),
    default=True,
)


# ============================================================
# REQUEST LIMITS
# ============================================================

MAX_REQUEST_BODY_SIZE = int(
    os.getenv(
        "MAX_REQUEST_BODY_SIZE",
        "1048576",
    )
)

if MAX_REQUEST_BODY_SIZE <= 0:

    raise RuntimeError(
        "MAX_REQUEST_BODY_SIZE must be greater than zero."
    )


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "Workforce Management Platform",
).strip()


APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
).strip()