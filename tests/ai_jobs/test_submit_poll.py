from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_chat_submit_and_poll():
    client = _client()
    res = client.post(
        "/api/v1/ai/jobs/chat",
        json={"messages": [{"role": "user", "content": "hola"}]},
    )
    assert res.status_code == 202
    data = res.json()
    res2 = client.get(data["status_url"])
    assert res2.status_code == 200
    body = res2.json()
    assert body["state"] == "SUCCESS"
    assert body["result"]["reply"] == "simulated response"


def test_failure_path(monkeypatch):
    from app.background import tasks as bg_tasks

    class BadClient:
        def chat(self, user_id, messages, model=None):  # noqa: D401
            raise ValueError("boom")

        def embeddings(self, user_id, texts):  # pragma: no cover - not used
            return []

    monkeypatch.setattr(bg_tasks, "get_ai_client", lambda: BadClient())
    client = _client()
    res = client.post(
        "/api/v1/ai/jobs/chat",
        json={"messages": [{"role": "user", "content": "hola"}]},
    )
    assert res.status_code == 202
    data = res.json()
    res2 = client.get(data["status_url"])
    body = res2.json()
    assert body["state"] == "FAILURE"
    assert "boom" in body["error"]


def test_idempotency_key():
    client = _client()
    headers = {"Idempotency-Key": "abc"}
    res1 = client.post(
        "/api/v1/ai/jobs/embeddings",
        json={"texts": ["one"]},
        headers=headers,
    )
    res2 = client.post(
        "/api/v1/ai/jobs/embeddings",
        json={"texts": ["two"]},
        headers=headers,
    )
    assert res1.status_code == 202 and res2.status_code == 202
    assert res1.json()["task_id"] == res2.json()["task_id"]
