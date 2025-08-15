import pytest
from datetime import date

from tests.utils.query_counter import count_queries
from app.core.database import engine
from app.user_profile.models import ActivityLevel, Goal


def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def auth_headers_user_a(tokens):
    return auth_headers(tokens)


@pytest.fixture
def seed_routines_data(test_client, auth_headers_user_a):
    routine_payload = {
        "name": "Routine",
        "days": [
            {
                "weekday": 0,
                "exercises": [{"exercise_name": "Push", "sets": 1, "reps": 1}],
            }
        ],
    }
    for i in range(2):
        data = routine_payload | {"name": f"Routine {i}"}
        res = test_client.post(
            "/api/v1/routines/",
            json=data,
            headers=auth_headers_user_a,
        )
        assert res.status_code == 200


@pytest.fixture
def seed_meals_data(test_client, auth_headers_user_a):
    profile_payload = {
        "full_name": "John",
        "age": 30,
        "height_cm": 180,
        "weight_kg": 80,
        "activity_level": ActivityLevel.SEDENTARY.value,
        "goal": Goal.MAINTAIN_WEIGHT.value,
    }
    test_client.post(
        "/api/v1/profiles/",
        json=profile_payload,
        headers=auth_headers_user_a,
    )
    day = str(date.today())
    meal_payload = {
        "date": day,
        "meal_type": "lunch",
        "items": [
            {
                "food_name": "Chicken",
                "serving_qty": 100,
                "serving_unit": "g",
                "calories_kcal": 100,
                "protein_g": 20,
                "carbs_g": 0,
                "fat_g": 2,
            },
            {
                "food_name": "Rice",
                "serving_qty": 100,
                "serving_unit": "g",
                "calories_kcal": 130,
                "protein_g": 2,
                "carbs_g": 28,
                "fat_g": 1,
            },
        ],
    }
    res = test_client.post(
        "/api/v1/nutrition/meal",
        json=meal_payload,
        headers=auth_headers_user_a,
    )
    assert res.status_code == 201
    # ensure target exists to avoid extra queries during measurement
    test_client.get(
        f"/api/v1/nutrition/targets?date={day}", headers=auth_headers_user_a
    )


def test_list_routines_queries_are_minimal(
    test_client, seed_routines_data, auth_headers_user_a
):
    with count_queries(engine) as qc:
        res = test_client.get("/api/v1/routines", headers=auth_headers_user_a)
        assert res.status_code == 200
    assert qc["n"] == 4, f"Queries inesperadas: {qc['n']}\n{qc['stmts'][:5]}"


def test_day_log_queries_are_minimal(test_client, seed_meals_data, auth_headers_user_a):
    day = str(date.today())
    with count_queries(engine) as qc:
        res = test_client.get(
            f"/api/v1/nutrition?date={day}", headers=auth_headers_user_a
        )
        assert res.status_code == 200
    assert qc["n"] == 5, f"Queries inesperadas: {qc['n']}\n{qc['stmts'][:5]}"
