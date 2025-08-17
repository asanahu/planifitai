import pytest
from fastapi.testclient import TestClient

from app.services.rules_engine import IMPACT_WORDS
from app.training import planner


def test_generate_basic(test_client: TestClient):
    payload = {
        "objective": "strength",
        "level": "beginner",
        "frequency": 3,
        "session_minutes": 25,
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert len(body["data"]["days"]) == 3


def test_restriction_knee(test_client: TestClient):
    payload = {
        "objective": "strength",
        "level": "beginner",
        "frequency": 3,
        "session_minutes": 25,
        "restrictions": ["rodilla"],
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    for day in data["days"]:
        for block in day["blocks"]:
            for ex in block["exercises"]:
                assert all(w not in ex["name"].lower() for w in IMPACT_WORDS)


def test_invalid_frequency(test_client: TestClient):
    payload = {
        "objective": "strength",
        "level": "beginner",
        "frequency": 7,
        "session_minutes": 25,
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 400
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PLAN_INVALID_FREQ"


def test_unknown_objective(test_client: TestClient):
    payload = {
        "objective": "hypertrophy",
        "level": "beginner",
        "frequency": 3,
        "session_minutes": 25,
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PLAN_NOT_FOUND"


def test_ai_fallback(monkeypatch):
    def fake_refine(plan_dict, context):
        plan = plan_dict.copy()
        plan.setdefault("meta", {})["note"] = "AI fallback"
        return plan

    monkeypatch.setattr("app.training.ai_generator.refine_with_ai", fake_refine)
    plan = planner.generate_plan_v2("strength", "advanced", 3, 30, [], use_ai=True)
    assert plan.meta.get("source") in {"rules", "ai"}
