"""
Quick local test for the AI nutrition plan endpoint.

Runs entirely offline using SQLite and `simulate=true` so it does not
require network nor an OpenRouter key. It creates a temporary user,
obtains a bearer token, and calls the endpoint.

Usage:

  uv venv (optional)
  export AI_FEATURES_ENABLED=true
  python scripts/test_ai_nutrition.py

To test with OpenRouter, set OPENROUTER_KEY and call without simulate=true
from your HTTP client against a running server.
"""

from __future__ import annotations

import os
from typing import Any


def main() -> None:
    # Ensure AI routes are enabled and DB is local SQLite for this test
    os.environ.setdefault("AI_FEATURES_ENABLED", "true")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai.db")

    # Lazy imports after env vars are set
    from app.core.database import Base, engine, SessionLocal
    import app.auth.models  # noqa: F401  # register tables
    import app.nutrition.models  # noqa: F401
    import app.ai.embeddings  # noqa: F401

    Base.metadata.create_all(bind=engine)

    from app.auth import services as auth_services
    from app.main import create_app
    from fastapi.testclient import TestClient

    # Create a user and token
    db = SessionLocal()
    try:
        user = auth_services.create_user(db, "test@example.com", "secret")
        token = auth_services.create_access_token({"sub": str(user.id)})
    finally:
        db.close()

    app = create_app()
    client = TestClient(app)

    payload: dict[str, Any] = {
        "days": 2,
        "preferences": {"diet": "mediterránea"},
    }

    res = client.post(
        "/api/v1/ai/generate/nutrition-plan?simulate=true",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    print("Status:", res.status_code)
    data = res.json()
    print("Keys:", list(data.keys()))
    print("Days:", len(data.get("days", [])))
    assert res.status_code == 200, data
    assert "days" in data and data["days"], "plan must contain days"
    print("OK: nutrition plan generated (simulated)")


if __name__ == "__main__":
    main()

