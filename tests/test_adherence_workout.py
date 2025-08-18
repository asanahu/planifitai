from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth.deps import UserContext, get_current_user
from app.auth.models import User
from app.core.database import Base, get_db
from app.main import app
from app.progress import models as progress_models
from app.routines import models as routine_models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return UserContext(id=1, email="t@example.com")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


@pytest.fixture()
def seed_user(db_session: Session):
    user = User(id=1, email="t@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    return user


def test_adherence_happy_path(test_client: TestClient, db_session: Session, seed_user):
    routine = routine_models.Routine(
        owner_id=seed_user.id,
        name="R",
        active_days={"mon": True, "wed": True, "fri": True, "sat": True},
    )
    db_session.add(routine)
    db_session.commit()

    week_start = date(2024, 8, 5)
    entries = [
        progress_models.ProgressEntry(
            user_id=seed_user.id,
            date=week_start,
            metric=progress_models.MetricEnum.workout,
            value=1,
        ),
        progress_models.ProgressEntry(
            user_id=seed_user.id,
            date=week_start + timedelta(days=2),
            metric=progress_models.MetricEnum.workout,
            value=1,
        ),
        progress_models.ProgressEntry(
            user_id=seed_user.id,
            date=week_start + timedelta(days=4),
            metric=progress_models.MetricEnum.workout,
            value=1,
        ),
    ]
    db_session.add_all(entries)
    db_session.commit()

    resp = test_client.get(
        f"/api/v1/routines/{routine.id}/adherence?range=custom&start={week_start}"
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data", body)
    assert data["planned"] == 4
    assert data["completed"] == 3
    assert data["adherence_pct"] == 75
    assert data["status"] == "ok"


def test_adherence_no_plan(test_client: TestClient, db_session: Session, seed_user):
    routine = routine_models.Routine(owner_id=seed_user.id, name="R2", active_days={})
    db_session.add(routine)
    db_session.commit()

    week_start = date(2024, 8, 5)
    resp = test_client.get(
        f"/api/v1/routines/{routine.id}/adherence?range=custom&start={week_start}"
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data", body)
    assert data["planned"] == 0
    assert data["completed"] == 0
    assert data["adherence_pct"] == 0
    assert data["status"] == "no_planned"


def test_adherence_respects_start_date(
    test_client: TestClient, db_session: Session, seed_user
):
    routine = routine_models.Routine(
        owner_id=seed_user.id,
        name="R3",
        active_days={"mon": True, "wed": True, "fri": True},
        start_date=date(2024, 8, 7),
    )
    db_session.add(routine)
    db_session.commit()

    week_start = date(2024, 8, 5)
    entries = [
        progress_models.ProgressEntry(
            user_id=seed_user.id,
            date=week_start + timedelta(days=2),
            metric=progress_models.MetricEnum.workout,
            value=1,
        ),
        progress_models.ProgressEntry(
            user_id=seed_user.id,
            date=week_start + timedelta(days=4),
            metric=progress_models.MetricEnum.workout,
            value=1,
        ),
    ]
    db_session.add_all(entries)
    db_session.commit()

    resp = test_client.get(
        f"/api/v1/routines/{routine.id}/adherence?range=custom&start={week_start}"
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data", body)
    assert data["planned"] == 2
    assert data["completed"] == 2
    assert data["adherence_pct"] == 100


def test_adherence_invalid_range(
    test_client: TestClient, db_session: Session, seed_user
):
    routine = routine_models.Routine(owner_id=seed_user.id, name="R4")
    db_session.add(routine)
    db_session.commit()
    resp = test_client.get(f"/api/v1/routines/{routine.id}/adherence?range=foo")
    assert resp.status_code == 422


def test_adherence_custom_start_normalizes(
    test_client: TestClient, db_session: Session, seed_user
):
    routine = routine_models.Routine(owner_id=seed_user.id, name="R5")
    db_session.add(routine)
    db_session.commit()

    start = date(2024, 8, 6)  # Tuesday
    resp = test_client.get(
        f"/api/v1/routines/{routine.id}/adherence?range=custom&start={start}"
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data", body)
    assert data["week_start"] == "2024-08-05"
    assert data["week_end"] == "2024-08-11"


def test_adherence_routine_not_found(
    test_client: TestClient, db_session: Session, seed_user
):
    resp = test_client.get("/api/v1/routines/999/adherence")
    assert resp.status_code == 404
