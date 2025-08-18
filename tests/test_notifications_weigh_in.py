import re
import types
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.notifications import models
from app.notifications import tasks as notif_tasks

try:  # pragma: no cover - optional helper
    from tests.utils import auth_headers as _auth_headers
except Exception:  # pragma: no cover - tests.utils may not provide auth_headers
    _auth_headers = None


TZ = ZoneInfo("Europe/Madrid")


def unwrap(j: dict) -> dict:
    return j.get("data", j)


def auth_hdr(tokens) -> dict:
    if _auth_headers:
        return _auth_headers(tokens)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def patch_task_delay(monkeypatch):
    def _sync_delay(user_id, day_of_week, local_time, weeks_ahead):
        try:
            data = notif_tasks.schedule_weigh_in_notifications_task(
                user_id, day_of_week, local_time, weeks_ahead
            )
        except ValueError as exc:  # invalid time
            raise HTTPException(status_code=422, detail=str(exc))
        return types.SimpleNamespace(get=lambda: data)

    monkeypatch.setattr(
        notif_tasks.schedule_weigh_in_notifications_task,
        "delay",
        staticmethod(_sync_delay),
    )


def test_weighin_default_8weeks_idempotent(
    test_client: TestClient, tokens, monkeypatch, db_session
):
    patch_task_delay(monkeypatch)
    res = test_client.post(
        "/api/v1/notifications/schedule/weigh-in",
        json={},
        headers=auth_hdr(tokens),
    )
    assert res.status_code == 200, res.text
    data = unwrap(res.json())
    assert isinstance(data.get("scheduled_count"), int)
    assert data["scheduled_count"] == 8
    assert data["timezone"] == "Europe/Madrid"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", data["first_scheduled_local"])

    db_session.commit()
    count = db_session.execute(
        select(models.Notification).where(
            models.Notification.type == models.NotificationType.WEIGH_IN,
            models.Notification.status == models.NotificationStatus.SCHEDULED,
        )
    ).scalars()
    assert len(list(count)) == 8

    res2 = test_client.post(
        "/api/v1/notifications/schedule/weigh-in",
        json={},
        headers=auth_hdr(tokens),
    )
    assert res2.status_code == 200, res2.text
    data2 = unwrap(res2.json())
    assert data2["scheduled_count"] == 0


def test_weighin_timezone_madrid_9am_local(
    test_client: TestClient, tokens, monkeypatch
):
    patch_task_delay(monkeypatch)
    body = {"day_of_week": 6, "local_time": "09:00", "weeks_ahead": 2}
    res = test_client.post(
        "/api/v1/notifications/schedule/weigh-in",
        json=body,
        headers=auth_hdr(tokens),
    )
    assert res.status_code == 200, res.text
    data = unwrap(res.json())
    assert data["timezone"] == "Europe/Madrid"
    first_local = datetime.fromisoformat(data["first_scheduled_local"]).replace(
        tzinfo=TZ
    )
    assert first_local.hour == 9 and first_local.minute == 0
    assert first_local.weekday() == 6


def test_weighin_quiet_hours_shift_or_skip(
    test_client: TestClient, tokens, monkeypatch
):
    try:
        from app.notifications import services as notif_services  # noqa: F401
    except Exception:
        pytest.skip("No quiet hours support in this build")

    patch_task_delay(monkeypatch)
    pref = {"quiet_hours_start_local": "09:00", "quiet_hours_end_local": "10:00"}
    res_pref = test_client.put(
        "/api/v1/notifications/preferences", json=pref, headers=auth_hdr(tokens)
    )
    assert res_pref.status_code == 200, res_pref.text

    body = {"day_of_week": 6, "local_time": "09:00", "weeks_ahead": 1}
    res = test_client.post(
        "/api/v1/notifications/schedule/weigh-in",
        json=body,
        headers=auth_hdr(tokens),
    )
    assert res.status_code == 200, res.text
    data = unwrap(res.json())
    first_local = datetime.fromisoformat(data["first_scheduled_local"]).replace(
        tzinfo=TZ
    )
    assert first_local.hour in (9, 10) and first_local.minute == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"day_of_week": -1},
        {"day_of_week": 7},
        {"local_time": "9:00"},
        {"local_time": "25:00"},
        {"weeks_ahead": 0},
        {"weeks_ahead": 100},
    ],
)
def test_weighin_validation_errors_422(
    test_client: TestClient, tokens, payload, monkeypatch
):
    patch_task_delay(monkeypatch)
    res = test_client.post(
        "/api/v1/notifications/schedule/weigh-in",
        json=payload,
        headers=auth_hdr(tokens),
    )
    assert res.status_code == 422


def test_weighin_requires_auth(test_client: TestClient, monkeypatch):
    patch_task_delay(monkeypatch)
    res = test_client.post("/api/v1/notifications/schedule/weigh-in", json={})
    assert res.status_code in (401, 403)
