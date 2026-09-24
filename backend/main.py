import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.logging_config import (
    setup_logging,
    request_id_context,
)

from backend.database import Base, engine

from backend.models import Employee
from backend.department_models import Department
from backend.attendance_models import Attendance
from backend.task_models import Task
from backend.user_models import User
from backend.audit_models import AuditLog
from backend.notification_models import Notification

from backend.routers import employees
from backend.routers import departments
from backend.routers import attendance
from backend.routers import tasks
from backend.routers import reports
from backend.routers import auth
from backend.routers import audit_logs
from backend.routers import notifications

from backend.config import (
    ENVIRONMENT,
    DEBUG,
    ALLOWED_ORIGINS,
    ALLOWED_HOSTS,
)


# ============================================================
# LOGGING
# ============================================================

setup_logging()

logger = logging.getLogger(__name__)


# ============================================================
# TESTING MODE
# ============================================================

TESTING = os.getenv(
    "TESTING",
    "0",
).lower() in {
    "1",
    "true",
    "yes",
}


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Workforce Management Platform",
    version="1.0.0",
    debug=DEBUG,
)


# ============================================================
# PRODUCTION HOST PROTECTION
# ============================================================

if ENVIRONMENT == "production":

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )


# ============================================================
# RATE LIMITING
# ============================================================

limiter = Limiter(
    key_func=get_remote_address,
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID",
    ],
)


# ============================================================
# SAFE ERROR HANDLERS
# ============================================================

@app.exception_handler(
    StarletteHTTPException
)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    """
    Return safe HTTP errors without exposing
    internal implementation details.
    """

    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(
            uuid.uuid4()
        )

    # Keep expected client errors safe.
    if isinstance(exc.detail, str):
        detail = exc.detail
    else:
        detail = "Request could not be completed."

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "request_id": request_id,
        },
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    if exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value

    return response


@app.exception_handler(
    RequestValidationError
)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Return safe validation errors.

    Do not expose server internals, SQL statements,
    file paths, passwords, tokens, or stack traces.
    """

    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(
            uuid.uuid4()
        )

    errors = []

    for error in exc.errors():

        location = ".".join(
            str(item)
            for item in error.get(
                "loc",
                [],
            )
        )

        errors.append(
            {
                "field": location,
                "message": error.get(
                    "msg",
                    "Invalid value",
                ),
                "type": error.get(
                    "type",
                    "validation_error",
                ),
            }
        )

    response = JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors,
            "request_id": request_id,
        },
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response


@app.exception_handler(
    Exception
)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Catch unexpected server errors.

    Detailed exception information is written only
    to server logs. The client receives a generic
    safe response.
    """

    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(
            uuid.uuid4()
        )

    logger.exception(
        "Unhandled application exception",
        extra={
            "request_method": request.method,
            "request_path": request.url.path,
            "status_code": 500,
            "request_id": request_id,
        },
    )

    response = JSONResponse(
        status_code=500,
        content={
            "detail": (
                "An internal server error occurred. "
                "Please try again later."
            ),
            "request_id": request_id,
        },
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.middleware("http")
async def security_headers(
    request: Request,
    call_next,
):
    response = await call_next(
        request
    )

    # Prevent MIME sniffing
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    # Prevent clickjacking
    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    # Referrer protection
    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    # Browser permissions
    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=()"
    )

    # Content Security Policy
    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # HSTS only in production
    if ENVIRONMENT == "production":

        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response


# ============================================================
# AUTHENTICATION RATE LIMITING
# ============================================================

AUTH_RATE_LIMIT = 5
AUTH_RATE_WINDOW = 60

auth_request_log = {}


@app.middleware("http")
async def authentication_rate_limit(
    request: Request,
    call_next,
):
    protected_paths = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/change-password",
    }

    # Testing bypass
    if TESTING:

        return await call_next(
            request
        )

    if (
        request.method == "POST"
        and request.url.path in protected_paths
    ):

        client_ip = get_remote_address(
            request
        )

        current_time = time.time()

        previous_requests = (
            auth_request_log.get(
                client_ip,
                [],
            )
        )

        # Keep only requests inside
        # the current rate-limit window.
        previous_requests = [
            timestamp
            for timestamp in previous_requests
            if (
                current_time - timestamp
                < AUTH_RATE_WINDOW
            )
        ]

        if (
            len(previous_requests)
            >= AUTH_RATE_LIMIT
        ):

            logger.warning(
                "Authentication rate limit exceeded",
                extra={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "status_code": 429,
                },
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many authentication "
                        "requests. Please try again later."
                    )
                },
                headers={
                    "Retry-After": str(
                        AUTH_RATE_WINDOW
                    )
                },
            )

        previous_requests.append(
            current_time
        )

        auth_request_log[
            client_ip
        ] = previous_requests

    return await call_next(
        request
    )


# ============================================================
# STRUCTURED REQUEST LOGGING + REQUEST ID
# ============================================================

@app.middleware("http")
async def log_requests(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(
            uuid.uuid4()
        )

    request_id_context.set(
        request_id
    )

    start_time = time.perf_counter()

    try:

        response = await call_next(
            request
        )

        duration = (
            time.perf_counter()
            - start_time
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        logger.info(
            "HTTP request completed",
            extra={
                "request_method": request.method,
                "request_path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": round(
                    duration,
                    4,
                ),
                "request_id": request_id,
            },
        )

        return response

    except Exception:

        duration = (
            time.perf_counter()
            - start_time
        )

        logger.exception(
            "Unhandled error during HTTP request",
            extra={
                "request_method": request.method,
                "request_path": request.url.path,
                "status_code": 500,
                "duration_seconds": round(
                    duration,
                    4,
                ),
                "request_id": request_id,
            },
        )

        raise

    finally:

        request_id_context.set(
            "-"
        )


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    employees.router
)

app.include_router(
    reports.router
)

app.include_router(
    departments.router
)

app.include_router(
    attendance.router
)

app.include_router(
    tasks.router
)

app.include_router(
    auth.router
)

app.include_router(
    audit_logs.router
)

app.include_router(
    notifications.router
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/frontend",
    StaticFiles(
        directory="frontend",
        html=True,
    ),
    name="frontend",
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def home():

    logger.info(
        "Root API endpoint accessed"
    )

    return {
        "message": (
            "Workforce Management Platform "
            "API is running"
        )
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    logger.info(
        "Health check endpoint accessed"
    )

    return {
        "status": "healthy"
    }


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
async def startup_event():

    logger.info(
        "Workforce Management Platform "
        "started successfully"
    )