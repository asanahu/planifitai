import pytest
from fastapi.testclient import TestClient

from app.ai.provider import OpenAIProvider
from app.ai import embeddings
from app.ai.schemas import ChatMessage, ChatRequest


def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_generate_workout_plan_simulated(test_client: TestClient, tokens):
    resp = test_client.post(
        "/api/v1/ai/generate/workout-plan?simulate=true",
        json={"days_per_week": 3},
        headers=auth_headers(tokens),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["days"]


def test_chat_requires_auth(test_client: TestClient):
    resp = test_client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "hola"}]},
        headers={"Authorization": "Bearer BAD"},
    )
    assert resp.status_code == 401


def test_provider_budget_exceeded():
    provider = OpenAIProvider(budget_cents=1)
    provider.chat(1, [], simulate=True)
    with pytest.raises(Exception):
        provider.chat(1, [], simulate=True)


def test_embeddings_upsert_search(db_session):
    embeddings.upsert_embedding(db_session, "routine", "A", "Title A", {}, [1.0, 0.0])
    embeddings.upsert_embedding(db_session, "routine", "B", "Title B", {}, [0.9, 0.1])
    result = embeddings.search_similar(db_session, "routine", [1.0, 0.0], k=1)
    assert result[0]["ref_id"] == "A"


def test_alembic_upgrade_head(tmp_path):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    assert script.get_revision("e1a1c2d3e4f5") is not None
