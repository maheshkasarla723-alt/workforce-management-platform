import os
import sys
from pathlib import Path

import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.pool import StaticPool
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
#
# Production uses PostgreSQL.
# SQLite does not have PostgreSQL's JSONB type.
#
# For tests only, compile JSONB as SQLite JSON.
# The production model is NOT changed.
# ============================================================

@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_, compiler, **kwargs):
    return "JSON"


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = "sqlite://"


# ============================================================
# TEST ENGINE
# ============================================================

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# ============================================================
# SQLITE FOREIGN KEYS
# ============================================================

@event.listens_for(test_engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record
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
# CREATE TEST TABLES
# ============================================================

@pytest.fixture(
    scope="session",
    autouse=True
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


# ============================================================
# DATABASE SESSION
# ============================================================

@pytest.fixture()
def db_session():

    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# FASTAPI TEST CLIENT
# ============================================================

@pytest.fixture()
def client(db_session):

    def override_get_db():

        try:
            yield db_session

        finally:
            pass

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:

        yield test_client

    app.dependency_overrides.clear()