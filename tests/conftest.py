import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "secret")
from cryptography.fernet import Fernet

os.environ.setdefault("PHI_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("PHI_PROVIDER", "app")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, engine, get_db
from app.main import app


def pytest_sessionstart(session):
    os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
    os.environ.setdefault("CELERY_BROKER_URL", "memory://")
    os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")


def pytest_collection_modifyitems(config, items):
    if os.getenv("CELERY_TASK_ALWAYS_EAGER") == "1":
        skip_marker = pytest.mark.skip(reason="requires Redis broker")
        for item in items:
            if Path(item.fspath).parts and "ai_jobs" in Path(item.fspath).parts:
                item.add_marker(skip_marker)


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False, future=True
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def tokens(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "string"},
    )
    login_resp = test_client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "string"},
    )
    return login_resp.json()
