"""AI provider clients with budgeting and simulation support.

Includes:
- OpenAIProvider: lightweight simulated provider used in tests.
- OpenRouterProvider: real calls to OpenRouter (DeepSeek V3.1 free).
- OpenRouterBackupProvider: backup provider using GLM-4.5 Air free model.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings


class OpenAIProvider:
    """Very small wrapper around the OpenAI API.

    Only a tiny subset is implemented to keep tests lightweight. The real
    project would call ``openai`` or ``openai.AsyncClient`` here. For the
    exercises we support a ``simulate`` mode returning deterministic
    payloads and a basic per-user budget check.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        # Usar API_OPEN_AI si está disponible, sino OPENAI_API_KEY
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        self._client = OpenAI(api_key=api_key)
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

        if simulate:
            return {"reply": "simulated response"}

        # Verificar rate limit antes de hacer el request
        from app.ai.rate_limiter import check_rate_limit, record_api_request
        
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit alcanzado. Intenta más tarde.")
        
        try:
            # Usar el modelo configurado en settings para compatibilidad
            model_name = getattr(settings, "OPENAI_CHAT_MODEL", None) or "gpt-4o-mini"
            completion = self._client.chat.completions.create(
                model=model_name,
                messages=messages,
            )
            
            # Registrar el request exitoso
            record_api_request()
            
            reply = completion.choices[0].message.content or ""
            return {"reply": reply}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        """Return an embedding vector for ``text``.

        When simulating, a deterministic small vector is returned.
        """

        if simulate:
            # Very small, deterministic embedding for tests
            return [float(len(text) % 3), 0.1, 0.2]

        try:
            response = self._client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI embedding error: {exc}")


class OpenRouterProvider:
    """Provider for OpenRouter using the OpenAI SDK-compatible client.

    Uses the free model deepseek/deepseek-chat-v3.1:free by default.
    When simulate=True or no OPENROUTER_KEY is configured, falls back to
    deterministic responses for tests/local usage.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        # Usar API_OPEN_AI si está disponible, sino OPENAI_API_KEY
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        self._client = OpenAI(api_key=api_key)
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
                timeout=settings.OPENAI_TIMEOUT_S or 10,
                max_retries=1,
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

            # Verificar rate limit antes de hacer el request
            from app.ai.rate_limiter import check_rate_limit, record_api_request
            
            if not check_rate_limit():
                raise HTTPException(status_code=429, detail="Rate limit alcanzado. Intenta más tarde.")
            
            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=model or settings.OPENROUTER_CHAT_MODEL,
                messages=messages,
                extra_headers=extra_headers or None,
            )
            
            # Registrar el request exitoso
            record_api_request()
            
            reply = completion.choices[0].message.content or ""
            return {"reply": reply}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {exc}")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        # Free DeepSeek model doesn't expose embeddings; keep simulated
        # deterministic small vector for now.
        return [float(len(text) % 3), 0.1, 0.2]


class OpenRouterBackupProvider:
    """Backup provider for OpenRouter using GLM-4.5 Air free model.
    
    This provider is used as a fallback when the main OpenRouterProvider
    hits rate limits or fails. Uses the same OpenRouter infrastructure
    but with a different API key and model.
    """

    def __init__(self, budget_cents: int | None = None) -> None:
        # Usar API_OPEN_AI si está disponible, sino OPENAI_API_KEY
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        self._client = OpenAI(api_key=api_key)
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
            if not settings.OPENROUTER_KEY2:
                raise HTTPException(status_code=503, detail="OpenRouter backup key not configured")
            self._client = OpenAI(
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_KEY2,
                timeout=settings.OPENAI_TIMEOUT_S or 10,
                max_retries=1,
            )

    def chat(
        self, user_id: int, messages: List[Dict[str, Any]], *, simulate: bool = False, model: str | None = None
    ) -> Dict[str, Any]:
        self._check_budget(user_id, cost=1)

        if simulate or not settings.OPENROUTER_KEY2:
            return {"reply": "simulated backup response"}

        self._ensure_client()
        try:
            extra_headers: Dict[str, str] = {}
            if settings.OPENROUTER_HTTP_REFERER:
                extra_headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER
            if settings.OPENROUTER_APP_TITLE:
                extra_headers["X-Title"] = settings.OPENROUTER_APP_TITLE

            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=model or settings.OPENROUTER_BACKUP_CHAT_MODEL,
                messages=messages,
                extra_headers=extra_headers or None,
            )
            reply = completion.choices[0].message.content or ""
            return {"reply": reply}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter backup error: {exc}")

    def embedding(self, text: str, *, simulate: bool = False) -> List[float]:
        # GLM-4.5 Air free model doesn't expose embeddings; keep simulated
        # deterministic small vector for now.
        return [float(len(text) % 3), 0.1, 0.2]
