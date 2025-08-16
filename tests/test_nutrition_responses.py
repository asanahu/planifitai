from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core.errors import (
    AUTH_FORBIDDEN,
    COMMON_HTTP,
    COMMON_VALIDATION,
    NUTRI_MEAL_NOT_FOUND,
)
from app.user_profile.models import ActivityLevel, Goal


def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def create_profile(client: TestClient, tokens):
    payload = {
        "full_name": "John Doe",
        "age": 30,
        "height_cm": 180,
        "weight_kg": 80,
        "activity_level": ActivityLevel.SEDENTARY.value,
        "goal": Goal.MAINTAIN_WEIGHT.value,
    }
    client.post("/api/v1/profiles/", json=payload, headers=auth_headers(tokens))


def test_create_meal_and_day(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    payload = {
        "date": str(date.today()),
        "meal_type": "lunch",
        "items": [],
    }
    res = test_client.post(
        "/api/v1/nutrition/meal",
        json=payload,
        headers=auth_headers(tokens),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["ok"] is True
    _meal_id = body["data"]["id"]

    res = test_client.get(
        f"/api/v1/nutrition?date={payload['date']}", headers=auth_headers(tokens)
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "totals" in body["data"]

    res = test_client.post(
        "/api/v1/nutrition/water",
        json={"datetime_utc": date.today().isoformat(), "volume_ml": 100},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["volume_ml"] == 100


def test_future_date_error(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    future = str(date.today() + timedelta(days=1))
    payload = {"date": future, "meal_type": "breakfast", "items": []}
    res = test_client.post(
        "/api/v1/nutrition/meal",
        json=payload,
        headers=auth_headers(tokens),
    )
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == COMMON_HTTP


def test_meal_not_found(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    res = test_client.patch(
        "/api/v1/nutrition/meal/999",
        json={"name": "x"},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == NUTRI_MEAL_NOT_FOUND


def test_validation_error(test_client: TestClient, tokens):
    res = test_client.post(
        "/api/v1/nutrition/meal",
        json={},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 422
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == COMMON_VALIDATION


def test_nutrition_forbidden(test_client: TestClient):
    res = test_client.get("/api/v1/nutrition", params={"date": str(date.today())})
    assert res.status_code in (401, 403)
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == AUTH_FORBIDDEN
