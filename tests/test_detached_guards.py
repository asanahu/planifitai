from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.auth import models as auth_models, services as auth_services
from app.auth.deps import UserContext, get_current_user
from app.routines import models as routine_models
from app.dependencies import get_owned_routine


def _override_user(user: auth_models.User):
    app.dependency_overrides[get_current_user] = lambda: UserContext(
        id=user.id, email=user.email, is_active=True
    )


def test_profile_create_no_detached(db_session: Session, test_client: TestClient):
    user = auth_models.User(email="u1@example.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()
    _override_user(user)
    payload = {
        "full_name": "Test User",
        "age": 30,
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "activity_level": "moderately_active",
        "goal": "maintain_weight",
    }
    resp = test_client.post("/api/v1/profiles/", json=payload)
    assert resp.status_code == 201
    assert resp.json()["full_name"] == payload["full_name"]
    app.dependency_overrides.clear()


def test_get_owned_routine_eager_loaded(db_session: Session):
    user = auth_models.User(id=1, email="r@example.com", hashed_password="pwd")
    routine = routine_models.Routine(id=1, owner_id=user.id, name="R")
    day = routine_models.RoutineDay(
        id=1, routine_id=routine.id, weekday=0, order_index=0
    )
    exercise = routine_models.RoutineExercise(
        id=1, routine_day_id=day.id, exercise_name="squat", sets=3
    )
    day.exercises.append(exercise)
    routine.days.append(day)
    db_session.add_all([user, routine, day, exercise])
    db_session.commit()
    ctx = UserContext(id=user.id, email=user.email, is_active=True)
    loaded = get_owned_routine(routine_id=routine.id, db=db_session, current_user=ctx)
    db_session.close()
    assert loaded.days[0].exercises[0].exercise_name == "squat"


def test_get_current_user_returns_dto(db_session: Session, test_client: TestClient):
    user = auth_models.User(email="dto@example.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()
    token = auth_services.create_access_token({"sub": str(user.id)})
    ctx = get_current_user(db=db_session, token=token)
    assert isinstance(ctx, UserContext)
    assert ctx.id == user.id
    assert ctx.email == user.email
    resp = test_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == user.id
