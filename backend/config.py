import os
from dotenv import load_dotenv


load_dotenv()


def get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).strip().lower()


DEBUG = get_bool(
    os.getenv("DEBUG"),
    default=False
)


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not configured."
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


ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]


ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]