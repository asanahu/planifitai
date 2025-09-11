from fastapi.testclient import TestClient


def test_next_week_basic_flow(test_client: TestClient):
    # Genera un plan inicial
    payload = {
        "objective": "strength",
        "level": "beginner",
        "frequency": 3,
        "session_minutes": 25,
        "use_ai": False,
    }
    res = test_client.post("/api/v1/training/generate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    plan = body["data"]

    # Avanza una semana
    res2 = test_client.post("/api/v1/training/next-week", json={"plan": plan})
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["ok"] is True
    next_plan = body2["data"]

    # Misma frecuencia
    assert len(next_plan["days"]) == payload["frequency"]
    # Se agrega/meta semana
    assert next_plan.get("meta", {}).get("week") == 2

