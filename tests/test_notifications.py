import datetime as dt

import pytest

from app.notifications import models, crud, schemas, tasks


@pytest.fixture
def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_preferences_save_and_get(test_client, auth_headers):
    data = {
        "tz": "Europe/Madrid",
        "channels_inapp": True,
        "channels_email": True,
        "quiet_hours_start_local": "22:00",
        "quiet_hours_end_local": "07:00",
    }
    resp = test_client.put("/api/v1/notifications/preferences", json=data, headers=auth_headers)
    assert resp.status_code == 200
    resp_get = test_client.get("/api/v1/notifications/preferences", headers=auth_headers)
    body = resp_get.json()
    assert body["tz"] == "Europe/Madrid"
    assert body["channels_email"] is True


def test_schedule_routine_and_dedupe(test_client, auth_headers):
    today = dt.date.today()
    weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][today.weekday()]
    active = {weekday: True}
    test_client.post(
        "/api/v1/notifications/schedule/routines",
        json={"routine_id": 1, "active_days": active, "hour_local": "09:00"},
        headers=auth_headers,
    )
    res = test_client.get("/api/v1/notifications", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    # schedule again -> dedupe
    test_client.post(
        "/api/v1/notifications/schedule/routines",
        json={"routine_id": 1, "active_days": active, "hour_local": "09:00"},
        headers=auth_headers,
    )
    res2 = test_client.get("/api/v1/notifications", headers=auth_headers)
    assert len(res2.json()) == 1


def test_quiet_hours_defer(test_client, auth_headers):
    pref = {
        "tz": "UTC",
        "quiet_hours_start_local": "22:00",
        "quiet_hours_end_local": "07:00",
    }
    test_client.put("/api/v1/notifications/preferences", json=pref, headers=auth_headers)
    today = dt.date.today()
    weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][today.weekday()]
    active = {weekday: True}
    test_client.post(
        "/api/v1/notifications/schedule/routines",
        json={"routine_id": 2, "active_days": active, "hour_local": "06:00"},
        headers=auth_headers,
    )
    res = test_client.get("/api/v1/notifications", headers=auth_headers)
    notif = res.json()[0]
    scheduled = dt.datetime.fromisoformat(notif["scheduled_at_utc"])
    assert scheduled.hour == 7


def test_schedule_nutrition(test_client, auth_headers):
    test_client.put("/api/v1/notifications/preferences", json={}, headers=auth_headers)
    test_client.post(
        "/api/v1/notifications/schedule/nutrition",
        json={"meal_times_local": {"breakfast": "09:00"}, "water_every_min": 60},
        headers=auth_headers,
    )
    res = test_client.get("/api/v1/notifications", headers=auth_headers)
    assert len(res.json()) >= 2  # meal + water


def test_dispatch_notification(test_client, auth_headers, db_session):
    pref = models.NotificationPreference(user_id=1)
    db_session.add(pref)
    db_session.commit()
    notif = crud.create_notification(
        db_session,
        schemas.NotificationCreate(
            user_id=1,
            category=models.NotificationCategory.SYSTEM,
            type=models.NotificationType.CUSTOM,
            title="Hi",
            body="Body",
            scheduled_at_utc=dt.datetime.utcnow(),
        ),
    )
    tasks.dispatch_notification_task.delay(notif.id)
    db_session.refresh(notif)
    assert notif.status == models.NotificationStatus.SENT
    assert "inapp" in notif.delivered_channels
