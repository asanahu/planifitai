"""OpenAI client abstraction with budgeting and simulation support."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import HTTPException

from app.core.config import settings


class OpenAIProvider:
    """Very small wrapper around the OpenAI API.

    Only a tiny subset is implemented to keep tests lightweight. The real
    project would call ``openai`` or ``openai.AsyncClient`` here. For the
    exercises we support a ``simulate`` mode returning deterministic
    payloads and a basic per-user budget check.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        self._spent = defaultdict(int)
        self._budget = budget_cents or settings.AI_DAILY_BUDGET_CENTS

    # ------------------------------------------------------------------ utils
    def _check_budget(self, user_id: int, cost: int) -> None:
        current = self._spent[user_id]
        if current + cost > self._budget:
            raise HTTPException(status_code=402, detail="AI budget exceeded")
        self._spent[user_id] = current + cost

    # ------------------------------------------------------------------ public
    def chat(
        self, user_id: int, messages: List[Dict[str, Any]], *, simulate: bool = False
    ) -> Dict[str, Any]:
        """Return a chat completion.

        In ``simulate`` mode a deterministic response is returned and no
        external API calls are performed. Each call consumes a small fixed
        cost for budgeting purposes.
        """

        self._check_budget(user_id, cost=1)

        if simulate or not settings.OPENAI_API_KEY:
            return {"reply": "simulated response"}

        # Real implementation would go here. For this kata we raise an error
        # so that tests use ``simulate=True``.
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        """Return an embedding vector for ``text``.

        When simulating, a deterministic small vector is returned.
        """

        if simulate or not settings.OPENAI_API_KEY:
            # Very small, deterministic embedding for tests
            return [float(len(text) % 3), 0.1, 0.2]

        raise HTTPException(status_code=503, detail="OpenAI client not configured")
