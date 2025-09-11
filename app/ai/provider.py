"""AI provider clients with budgeting and simulation support.

Includes:
- OpenAIProvider: lightweight simulated provider used in tests.
- OpenRouterProvider: real calls to OpenRouter (DeepSeek V3.1 free).
"""

from __future__ import annotations

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


class OpenRouterProvider:
    """Provider for OpenRouter using the OpenAI SDK-compatible client.

    Uses the free model deepseek/deepseek-chat-v3.1:free by default.
    When simulate=True or no OPENROUTER_KEY is configured, falls back to
    deterministic responses for tests/local usage.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        self._spent = defaultdict(int)
        self._budget = budget_cents or settings.AI_DAILY_BUDGET_CENTS
        # Lazy init of SDK to avoid import cost when unused
        self._client = None

    def _check_budget(self, user_id: int, cost: int) -> None:
        current = self._spent[user_id]
        if current + cost > self._budget:
            raise HTTPException(status_code=402, detail="AI budget exceeded")
        self._spent[user_id] = current + cost

    def _ensure_client(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore
            except Exception as exc:  # pragma: no cover - defensive
                raise HTTPException(status_code=500, detail="openai SDK missing") from exc
            if not settings.OPENROUTER_KEY:
                raise HTTPException(status_code=503, detail="OpenRouter key not configured")
            self._client = OpenAI(
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_KEY,
                timeout=settings.OPENAI_TIMEOUT_S or 30,
                max_retries=settings.OPENAI_RETRIES,
            )

    def chat(
        self, user_id: int, messages: List[Dict[str, Any]], *, simulate: bool = False, model: str | None = None
    ) -> Dict[str, Any]:
        self._check_budget(user_id, cost=1)

        if simulate or not settings.OPENROUTER_KEY:
            return {"reply": "simulated response"}

        self._ensure_client()
        try:
            extra_headers: Dict[str, str] = {}
            if settings.OPENROUTER_HTTP_REFERER:
                extra_headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER
            if settings.OPENROUTER_APP_TITLE:
                extra_headers["X-Title"] = settings.OPENROUTER_APP_TITLE

            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=model or settings.OPENROUTER_CHAT_MODEL,
                messages=messages,
                extra_headers=extra_headers or None,
            )
            reply = completion.choices[0].message.content or ""
            return {"reply": reply}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {exc}")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        # Free DeepSeek model doesn't expose embeddings; keep simulated
        # deterministic small vector for now.
        return [float(len(text) % 3), 0.1, 0.2]
