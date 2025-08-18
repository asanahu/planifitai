from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.auth.models import User
from app.progress.models import MetricEnum, ProgressEntry
from app.routines import schemas as routine_schemas
from app.routines.models import Routine
from app.utils.datetimes import week_bounds

TZ = ZoneInfo("Europe/Madrid")

# Ensure Pydantic v2 allows ORM mode for RoutineRead
routine_schemas.RoutineRead.model_config["from_attributes"] = True
routine_schemas.RoutineRead.from_orm = classmethod(
    lambda cls, obj: cls.model_validate(obj, from_attributes=True)
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def unwrap(json_obj):
    """Return payload under "data" if API envelope is used."""
    return json_obj.get("data", json_obj)


def get_pct(adherence):
    return adherence.get("adherence_pct", adherence.get("percentage"))


def mk_local(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=TZ)


def to_utc(dt_local: datetime) -> datetime:
    return dt_local.astimezone(ZoneInfo("UTC"))


def ensure_routine(db_session, user: User, active_days: dict | None = None) -> Routine:
    routine = Routine(owner_id=user.id, name="R", active_days=active_days or {})
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)
    return routine


def ensure_progress(db_session, user: User, dt_local: datetime) -> ProgressEntry:
    entry = ProgressEntry(
        user_id=user.id,
        date=dt_local.date(),
        metric=MetricEnum.workout,
        value=1,
    )
    db_session.add(entry)
    db_session.commit()
    return entry


def _week_bounds_this():
    return week_bounds("this_week", tz=str(TZ))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def user(db_session, tokens):
    return db_session.query(User).filter_by(email="user@example.com").one()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_detail_includes_adherence_this_week_happy_path(
    test_client, db_session, user, auth_headers
):
    active_days = {"mon": True, "wed": True, "fri": True, "sat": True}
    routine = ensure_routine(db_session, user, active_days)
    week_start, _ = _week_bounds_this()
    monday = mk_local(week_start.year, week_start.month, week_start.day, 10)
    wednesday = monday + timedelta(days=2)
    friday = monday + timedelta(days=4)
    ensure_progress(db_session, user, monday)
    ensure_progress(db_session, user, wednesday)
    ensure_progress(db_session, user, friday)

    resp = test_client.get(
        f"/api/v1/routines/{routine.id}?week=this", headers=auth_headers
    )
    assert resp.status_code == 200
    payload = unwrap(resp.json())
    assert "adherence" in payload
    adherence = payload["adherence"]
    assert adherence["planned"] == 4
    assert adherence["completed"] == 3
    assert get_pct(adherence) in {75, 75.0}


def test_detail_last_week_no_planned(test_client, db_session, user, auth_headers):
    routine = ensure_routine(db_session, user, active_days={})
    resp = test_client.get(
        f"/api/v1/routines/{routine.id}?week=last", headers=auth_headers
    )
    assert resp.status_code == 200
    adherence = unwrap(resp.json())["adherence"]
    assert adherence["planned"] == 0
    assert adherence["completed"] == 0
    assert get_pct(adherence) in {0, 0.0}
    assert "no_planned" in str(adherence.get("status"))


def test_detail_custom_requires_dates(test_client, db_session, user, auth_headers):
    routine = ensure_routine(db_session, user)
    resp = test_client.get(
        f"/api/v1/routines/{routine.id}?week=custom", headers=auth_headers
    )
    assert resp.status_code == 422
    resp2 = test_client.get(
        f"/api/v1/routines/{routine.id}?week=custom&start=2030-01-08&end=2030-01-01",
        headers=auth_headers,
    )
    assert resp2.status_code == 422


def test_tz_boundaries_madrid(test_client, db_session, user, auth_headers):
    routine = ensure_routine(db_session, user, {"mon": True, "sun": True})
    week_start, _ = _week_bounds_this()
    sunday_prev = week_start - timedelta(days=1)
    ensure_progress(
        db_session,
        user,
        mk_local(sunday_prev.year, sunday_prev.month, sunday_prev.day, 23, 59, 30),
    )
    ensure_progress(
        db_session,
        user,
        mk_local(week_start.year, week_start.month, week_start.day, 0, 0, 30),
    )

    resp_this = test_client.get(
        f"/api/v1/routines/{routine.id}?week=this", headers=auth_headers
    )
    assert resp_this.status_code == 200
    adherence_this = unwrap(resp_this.json())["adherence"]
    assert adherence_this["completed"] == 1

    resp_last = test_client.get(
        f"/api/v1/routines/{routine.id}?week=last", headers=auth_headers
    )
    assert resp_last.status_code == 200
    adherence_last = unwrap(resp_last.json())["adherence"]
    assert adherence_last["completed"] == 1


def test_routine_not_found_404(test_client, auth_headers):
    resp = test_client.get("/api/v1/routines/999999?week=this", headers=auth_headers)
    assert resp.status_code in {404, 422}
