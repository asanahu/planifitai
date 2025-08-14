from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

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


def test_create_meal_and_day_log(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    meal_payload = {
        "date": str(date.today()),
        "meal_type": "lunch",
        "name": "Poke de pollo",
        "items": [
            {
                "food_name": "Pechuga de pollo",
                "serving_qty": 150,
                "serving_unit": "g",
                "calories_kcal": 247,
                "protein_g": 46.5,
                "carbs_g": 0,
                "fat_g": 5,
            },
            {
                "food_name": "Arroz cocido",
                "serving_qty": 180,
                "serving_unit": "g",
                "calories_kcal": 234,
                "protein_g": 4.5,
                "carbs_g": 50.4,
                "fat_g": 0.6,
            },
        ],
    }
    res = test_client.post("/api/v1/nutrition/meal", json=meal_payload, headers=auth_headers(tokens))
    assert res.status_code == 201
    res = test_client.get(f"/api/v1/nutrition?date={meal_payload['date']}", headers=auth_headers(tokens))
    data = res.json()
    assert float(data["totals"]["calories_kcal"]) == 481
    assert data["water_total_ml"] == 0
    assert data["targets"]["source"] == "auto"


def test_future_date_validation(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    future = str(date.today() + timedelta(days=1))
    meal_payload = {
        "date": future,
        "meal_type": "breakfast",
        "items": [],
    }
    res = test_client.post("/api/v1/nutrition/meal", json=meal_payload, headers=auth_headers(tokens))
    assert res.status_code == 400


def test_water_logs(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    now = datetime.utcnow().isoformat()
    res = test_client.post(
        "/api/v1/nutrition/water",
        json={"datetime_utc": now, "volume_ml": 250},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 201
    day = str(date.today())
    res = test_client.get(f"/api/v1/nutrition/water?date={day}", headers=auth_headers(tokens))
    data = res.json()
    assert data["total_ml"] == 250
    assert len(data["logs"]) == 1


def test_targets_custom_and_recompute(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    day = str(date.today())
    res = test_client.get(f"/api/v1/nutrition/targets?date={day}", headers=auth_headers(tokens))
    assert res.status_code == 200
    auto = res.json()
    assert auto["source"] == "auto"
    custom_payload = {
        "date": day,
        "calories_target": 2300,
        "protein_g_target": 140,
        "carbs_g_target": 260,
        "fat_g_target": 70,
    }
    res = test_client.post(
        "/api/v1/nutrition/targets/custom", json=custom_payload, headers=auth_headers(tokens)
    )
    assert res.status_code == 200
    res = test_client.get(f"/api/v1/nutrition/targets?date={day}", headers=auth_headers(tokens))
    data = res.json()
    assert data["source"] == "custom"
    assert data["calories_target"] == 2300
    # recompute should keep custom
    res = test_client.post(
        f"/api/v1/nutrition/targets/auto/recompute?date={day}", headers=auth_headers(tokens)
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "custom"
    assert data["calories_target"] == 2300


def test_summary(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    day1 = str(date.today())
    day2 = str(date.today() - timedelta(days=1))
    meal_payload = {
        "date": day2,
        "meal_type": "breakfast",
        "items": [
            {
                "food_name": "Avena",
                "serving_qty": 100,
                "serving_unit": "g",
                "calories_kcal": 389,
                "protein_g": 16.9,
                "carbs_g": 66.3,
                "fat_g": 6.9,
            }
        ],
    }
    test_client.post("/api/v1/nutrition/meal", json=meal_payload, headers=auth_headers(tokens))
    meal_payload["date"] = day1
    test_client.post("/api/v1/nutrition/meal", json=meal_payload, headers=auth_headers(tokens))
    res = test_client.get(
        f"/api/v1/nutrition/summary?start={day2}&end={day1}", headers=auth_headers(tokens)
    )
    data = res.json()
    assert float(data["totals"]["calories_kcal"]) == 778
    assert float(data["average"]["calories_kcal"]) == 389


def test_post_daily_summary_and_progress(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    day = str(date.today())
    meal_payload = {
        "date": day,
        "meal_type": "lunch",
        "items": [
            {
                "food_name": "Pasta",
                "serving_qty": 100,
                "serving_unit": "g",
                "calories_kcal": 131,
                "protein_g": 5,
                "carbs_g": 25,
                "fat_g": 1.1,
            }
        ],
    }
    test_client.post("/api/v1/nutrition/meal", json=meal_payload, headers=auth_headers(tokens))
    test_client.post(
        "/api/v1/nutrition/water",
        json={"datetime_utc": datetime.utcnow().isoformat(), "volume_ml": 500},
        headers=auth_headers(tokens),
    )
    res = test_client.post(
        f"/api/v1/nutrition/post-daily-summary?date={day}", headers=auth_headers(tokens)
    )
    assert res.status_code == 200
    prog = test_client.get(
        f"/api/v1/progress?metric=calories_intake&start={day}&end={day}",
        headers=auth_headers(tokens),
    )
    entries = prog.json()
    assert entries[0]["value"] == 131
    water = test_client.get(
        f"/api/v1/progress?metric=water_ml&start={day}&end={day}", headers=auth_headers(tokens)
    )
    assert water.json()[0]["value"] == 500


def test_auth_and_forbidden(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    meal_payload = {
        "date": str(date.today()),
        "meal_type": "dinner",
        "items": [],
    }
    res = test_client.post("/api/v1/nutrition/meal", json=meal_payload)
    assert res.status_code == 401

    res = test_client.post(
        "/api/v1/nutrition/meal",
        json=meal_payload,
        headers=auth_headers(tokens),
    )
    meal_id = res.json()["id"]

    # second user
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "string"},
    )
    login = test_client.post(
        "/api/v1/auth/login", data={"username": "other@example.com", "password": "string"}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    # create profile for second user to satisfy dependencies
    create_profile(test_client, login.json())
    res = test_client.patch(
        f"/api/v1/nutrition/meal/{meal_id}",
        json={"name": "other"},
        headers=other_headers,
    )
    assert res.status_code == 404

def test_schedule_reminders(test_client: TestClient, tokens):
    create_profile(test_client, tokens)
    payload = {"breakfast": "09:00", "water_every_min": 120}
    res = test_client.post(
        "/api/v1/nutrition/schedule-reminders",
        json=payload,
        headers=auth_headers(tokens),
    )
    assert res.status_code == 200
    assert res.json()["scheduled"] is True
