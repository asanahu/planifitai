"""Simple AI provider for chat and embeddings."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from fastapi import HTTPException


class OpenAIProvider:
    """Tiny wrapper around the OpenAI API used for tests.

    The real project would call the official OpenAI client. Here we only
    implement a deterministic simulation mode so that tests can run without
    external calls.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        self._spent = defaultdict(int)
        self._budget = budget_cents or 100

    def _check_budget(self, user_id: int, cost: int) -> None:
        current = self._spent[user_id]
        if current + cost > self._budget:
            raise HTTPException(status_code=402, detail="AI budget exceeded")
        self._spent[user_id] = current + cost

    def chat(
        self, user_id: int, messages: List[Dict[str, Any]], *, simulate: bool = False
    ) -> Dict[str, Any]:
        """Return a chat completion."""
        self._check_budget(user_id, cost=1)
        if simulate:
            return {"reply": "simulated response", "usage": {}}
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        """Return an embedding vector for ``text``."""
        if simulate:
            return [float(len(text) % 3), 0.1, 0.2]
        raise HTTPException(status_code=503, detail="OpenAI client not configured")
