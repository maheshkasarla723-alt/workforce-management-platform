import os
import sys
from pathlib import Path

import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient


# ============================================================
# TESTING MODE
# ============================================================

os.environ["TESTING"] = "1"


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# SQLITE COMPATIBILITY FOR POSTGRESQL JSONB
# ============================================================

@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_, compiler, **kwargs):
    return "JSON"


# ============================================================
# TEST DATABASE
# ============================================================
#
# IMPORTANT:
# Do NOT use:
#
#     sqlite://
#     StaticPool
#
# because concurrent requests would share the same SQLite
# connection.
#
# A file-based SQLite database + QueuePool allows separate
# connections for concurrent requests.
# ============================================================

TEST_DATABASE_PATH = PROJECT_ROOT / "test_workforce.db"

TEST_DATABASE_URL = (
    f"sqlite:///{TEST_DATABASE_PATH}"
)


# ============================================================
# TEST ENGINE
# ============================================================

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)


# ============================================================
# SQLITE FOREIGN KEYS
# ============================================================

@event.listens_for(test_engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record,
):
    cursor = dbapi_connection.cursor()

    cursor.execute(
        "PRAGMA foreign_keys=ON"
    )

    cursor.close()


# ============================================================
# IMPORT APPLICATION
# ============================================================

from backend.main import app
from backend.database import Base, get_db


# ============================================================
# SESSION FACTORY
# ============================================================

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ============================================================
# CREATE TEST DATABASE
# ============================================================

@pytest.fixture(
    scope="session",
    autouse=True,
)
def create_test_database():

    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine
    )

    test_engine.dispose()

    if TEST_DATABASE_PATH.exists():
        try:
            TEST_DATABASE_PATH.unlink()
        except PermissionError:
            pass


# ============================================================
# DATABASE SESSION FOR TEST CODE
# ============================================================
#
# This session is ONLY for the test itself.
#
# It is NOT shared with FastAPI requests.
# ============================================================

@pytest.fixture()
def db_session():

    db = TestingSessionLocal()

    try:

        yield db

    finally:

        db.rollback()
        db.close()


# ============================================================
# FASTAPI TEST CLIENT
# ============================================================
#
# IMPORTANT:
#
# Every HTTP request gets a NEW SQLAlchemy Session.
#
# We do NOT use the db_session fixture here.
#
# This is what fixes the concurrency error.
# ============================================================

@pytest.fixture()
def client():

    def override_get_db():

        db = TestingSessionLocal()

        try:

            yield db

        except Exception:

            db.rollback()
            raise

        finally:

            db.close()


    app.dependency_overrides[
        get_db
    ] = override_get_db


    try:

        with TestClient(app) as test_client:

            yield test_client

    finally:

        app.dependency_overrides.clear()