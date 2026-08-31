import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./.pytest_webxpert.db")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-32b")
os.environ.setdefault("ADMIN_EMAIL", "admin@webxpert.com")
os.environ.setdefault("ADMIN_PASSWORD", "changeme")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.seed import seed


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
        yield db
    finally:
        db.close()


@pytest.fixture
def db(_reset_db) -> Session:
    return _reset_db


@pytest.fixture
def client(_reset_db) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@webxpert.com", "password": "changeme"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
