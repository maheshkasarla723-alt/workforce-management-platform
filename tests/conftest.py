import os
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient


# ------------------------------------------------------------
# TESTING MODE
# ------------------------------------------------------------

os.environ["TESTING"] = "1"


# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# DATABASE CONFIGURATION
# ------------------------------------------------------------
#
# Local development:
#     DATABASE_URL is read from .env
#
# GitHub Actions:
#     DATABASE_URL is provided by the CI workflow environment
# ------------------------------------------------------------

env_file = PROJECT_ROOT / ".env"

env_values = dotenv_values(env_file)

database_url = os.getenv("DATABASE_URL") or env_values.get(
    "DATABASE_URL"
)

if not database_url:
    raise ValueError(
        "DATABASE_URL is not configured. "
        "Set DATABASE_URL in .env or the CI environment."
    )


# ------------------------------------------------------------
# TEST DATABASE
# ------------------------------------------------------------
#
# Always use a separate test database.
# The tests will create/drop tables in this database only.
# ------------------------------------------------------------

test_database_url = make_url(database_url).set(
    database="workforce_management_test"
)

os.environ["DATABASE_URL"] = test_database_url.render_as_string(
    hide_password=False
)


# ------------------------------------------------------------
# IMPORT APPLICATION
# ------------------------------------------------------------

from backend.main import app
from backend.database import Base, engine, get_db


# ------------------------------------------------------------
# CREATE TEST DATABASE TABLES
# ------------------------------------------------------------

@pytest.fixture(
    scope="session",
    autouse=True
)
def create_test_database():

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )

    yield

    Base.metadata.drop_all(
        bind=engine
    )


# ------------------------------------------------------------
# DATABASE SESSION FIXTURE
# ------------------------------------------------------------

@pytest.fixture()
def db_session():

    from backend.database import SessionLocal

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ------------------------------------------------------------
# FASTAPI TEST CLIENT
# ------------------------------------------------------------

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