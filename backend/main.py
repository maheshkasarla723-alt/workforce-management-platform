import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.logging_config import (
    setup_logging,
    request_id_context
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
    "0"
).lower() in {
    "1",
    "true",
    "yes"
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
    version="1.0.0"
)


# ============================================================
# RATE LIMITING
# ============================================================

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# ============================================================
# CORS
# ============================================================

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5501",
    "http://localhost:5501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID"
    ]
)


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.middleware("http")
async def security_headers(
    request: Request,
    call_next
):
    response = await call_next(request)

    # Prevent browsers from MIME-sniffing responses
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    # Prevent the application from being embedded in frames
    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    # Control referrer information
    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    # Disable unnecessary browser capabilities
    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=()"
    )

    return response


# ============================================================
# AUTHENTICATION RATE-LIMITING MIDDLEWARE
# ============================================================

AUTH_RATE_LIMIT = 5
AUTH_RATE_WINDOW = 60

auth_request_log = {}


@app.middleware("http")
async def authentication_rate_limit(
    request: Request,
    call_next
):
    protected_paths = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/change-password"
    }

    # --------------------------------------------------------
    # TEST MODE
    # --------------------------------------------------------

    if TESTING:
        return await call_next(request)

    # --------------------------------------------------------
    # NORMAL APPLICATION MODE
    # --------------------------------------------------------

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
                []
            )
        )

        # Keep only requests from the last
        # AUTH_RATE_WINDOW seconds
        previous_requests = [
            timestamp
            for timestamp in previous_requests
            if (
                current_time - timestamp
                < AUTH_RATE_WINDOW
            )
        ]

        # Reject if limit is reached
        if len(previous_requests) >= AUTH_RATE_LIMIT:

            logger.warning(
                "Authentication rate limit exceeded",
                extra={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "status_code": 429
                }
            )

            from fastapi.responses import JSONResponse

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
                }
            )

        previous_requests.append(
            current_time
        )

        auth_request_log[
            client_ip
        ] = previous_requests

    return await call_next(request)


# ============================================================
# STRUCTURED REQUEST LOGGING + REQUEST ID
# ============================================================

@app.middleware("http")
async def log_requests(
    request: Request,
    call_next
):
    # Use client-provided request ID when available.
    # Otherwise generate a new UUID.
    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(
            uuid.uuid4()
        )

    # Store request ID in ContextVar so every log
    # generated during this request can use it.
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

        # Return request ID to the client.
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
                    4
                )
            }
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
                    4
                )
            }
        )

        raise

    finally:

        # Clear request context after request finishes.
        request_id_context.set("-")


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
        html=True
    ),
    name="frontend"
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