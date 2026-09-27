from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# PROJECT PATH
# ============================================================

# backend/database.py
# Project root = one level above the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT
# ============================================================

# Load .env from the project root
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# Also allow an environment variable supplied by the
# operating system / Render / deployment environment.
DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError(
        f"DATABASE_URL is not set. "
        f"Expected it in: {ENV_FILE}"
    )


# ============================================================
# DATABASE TIMEOUT CONFIGURATION
# ============================================================

DB_CONNECT_TIMEOUT = int(
    os.getenv(
        "DB_CONNECT_TIMEOUT_SECONDS",
        "10",
    )
)

DB_POOL_TIMEOUT = int(
    os.getenv(
        "DB_POOL_TIMEOUT_SECONDS",
        "30",
    )
)

DB_POOL_RECYCLE = int(
    os.getenv(
        "DB_POOL_RECYCLE_SECONDS",
        "1800",
    )
)

DB_STATEMENT_TIMEOUT = int(
    os.getenv(
        "DB_STATEMENT_TIMEOUT_MS",
        "30000",
    )
)


# ============================================================
# DATABASE ENGINE
# ============================================================

is_postgresql = DATABASE_URL.startswith(
    (
        "postgresql://",
        "postgresql+psycopg2://",
        "postgres://",
    )
)


if is_postgresql:

    engine = create_engine(
        DATABASE_URL,

        connect_args={
            "connect_timeout": DB_CONNECT_TIMEOUT,
            "options": (
                f"-c statement_timeout="
                f"{DB_STATEMENT_TIMEOUT}"
            ),
        },

        pool_pre_ping=True,
        pool_recycle=DB_POOL_RECYCLE,
        pool_timeout=DB_POOL_TIMEOUT,
    )

else:

    # SQLite / test database
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()