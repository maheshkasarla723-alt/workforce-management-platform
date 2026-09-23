import os
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient


# ============================================================
# TESTING MODE
# ============================================================

# Tell the application that pytest is running.
# This allows the authentication rate limiter to be bypassed
# during automated tests while remaining enabled normally.
os.environ["TESTING"] = "1"


# ============================================================
# PROJECT ROOT
# ============================================================

# conftest.py is located at:
#
# workforce management project/
# └── tests/
#     └── conftest.py
#
# parents[0] = tests
# parents[1] = project root
#
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# READ DATABASE URL FROM .ENV
# ============================================================

env_file = PROJECT_ROOT / ".env"

env_values = dotenv_values(env_file)

database_url = env_values.get("DATABASE_URL")

if not database_url:
    raise ValueError(
        f"DATABASE_URL is not set in .env file: {env_file}"
    )


# ============================================================
# USE SEPARATE TEST DATABASE
# ============================================================

test_database_url = make_url(
    database_url
).set(
    database="workforce_management_test"
)

os.environ["DATABASE_URL"] = (
    test_database_url.render_as_string(
        hide_password=False
    )
)


# ============================================================
# IMPORT APPLICATION AFTER ENVIRONMENT IS CONFIGURED
# ============================================================

from backend.main import app
from backend.database import Base, engine, get_db


# ============================================================
# CREATE CLEAN TEST DATABASE SCHEMA
# ============================================================

@pytest.fixture(
    scope="session",
    autouse=True
)
def create_test_database():

    # Remove existing test tables
    Base.metadata.drop_all(
        bind=engine
    )

    # Create fresh test tables
    Base.metadata.create_all(
        bind=engine
    )

    yield

    # Clean up after all tests
    Base.metadata.drop_all(
        bind=engine
    )


# ============================================================
# DATABASE SESSION
# ============================================================

@pytest.fixture()
def db_session():

    from backend.database import SessionLocal

    db = SessionLocal()

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