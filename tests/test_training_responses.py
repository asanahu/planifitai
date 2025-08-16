from fastapi.testclient import TestClient

from app.services.rules_engine import IMPACT_WORDS


def test_generate_3days(test_client: TestClient):
    payload = {"objective": "strength", "frequency": 3}
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["note"] == "IA pendiente"
    days = body["data"]["days"]
    assert len(days) == 3


def test_generate_with_restriction(test_client: TestClient):
    payload = {
        "objective": "strength",
        "frequency": 3,
        "restrictions": ["rodilla"],
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    days = body["data"]["days"]
    assert len(days) == 3
    for day in days:
        for ex in day["exercises"]:
            assert all(w not in ex.lower() for w in IMPACT_WORDS)
    assert body["data"]["note"] == "IA pendiente"


def test_invalid_frequency(test_client: TestClient):
    payload = {"objective": "strength", "frequency": 10}
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PLAN_INVALID_FREQ"


def test_unknown_objective(test_client: TestClient):
    payload = {"objective": "unknown", "frequency": 3}
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PLAN_NOT_FOUND"
