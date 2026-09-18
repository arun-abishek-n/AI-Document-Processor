"""Test-wide setup: points the app at an isolated, temporary SQLite file
instead of backend/data/app.db, so running the test suite never touches or
resets whatever data exists in the real local/dev database.

This module-level code (not a fixture) runs the moment pytest loads this
conftest — which happens before any test module imports app.database — so
config.DATABASE_URL picks up the override on its very first read.
"""

from __future__ import annotations

import os
import tempfile

_TEST_DB_FD, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_TEST_DB_FD)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-production"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seed_test_database():
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield
    engine.dispose()  # release the sqlite file handle before removing it (Windows locks open files)
    os.remove(_TEST_DB_PATH)


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return auth_headers(client, "admin", "admin123")


@pytest.fixture
def manager_headers(client):
    return auth_headers(client, "manager", "manager123")


@pytest.fixture
def executive_headers(client):
    return auth_headers(client, "executive", "executive123")


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
