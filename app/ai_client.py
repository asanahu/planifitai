"""Client for the external AI microservice with local fallback."""

from __future__ import annotations

import hmac
import json
import time
import uuid
from hashlib import sha256
from typing import Any, Dict, List, Optional

import httpx

from app.ai.provider import OpenAIProvider, OpenRouterProvider, OpenRouterBackupProvider
from app.core.config import settings


class AiClient:
    def __init__(
        self, base_url: str, secret: str, timeout: int = 120, max_retries: int = 1
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret = secret.encode()
        self._max_retries = max_retries
        self._client = httpx.Client(timeout=httpx.Timeout(timeout, connect=5, read=120))
        self._failures = 0
        self._next_retry = 0.0

    def _signed_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if time.time() < self._next_retry:
            raise httpx.RequestError("circuit open")

        body = json.dumps(payload, separators=(",", ":")).encode()
        ts = str(int(time.time()))
        sig = hmac.new(self._secret, f"{ts}.".encode() + body, sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Internal-Signature": sig,
            "X-Request-ID": str(uuid.uuid4()),
        }

        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client.post(
                    self._base_url + path, content=body, headers=headers
                )
                if resp.status_code >= 500:
                    raise httpx.HTTPError("server error")
                resp.raise_for_status()
                self._failures = 0
                return resp.json()
            except httpx.HTTPError:
                if attempt == self._max_retries:
                    self._failures += 1
                    if self._failures >= 3:
                        self._next_retry = time.time() + 30
                    raise
                time.sleep(2**attempt)
        raise RuntimeError("unreachable")

    # ------------------------------------------------------------------ public
    def embeddings(
        self, user_id: int, texts: List[str], *, simulate: bool = False
    ) -> List[List[float]]:
        payload = {"texts": texts}
        data = self._signed_post("/v1/embeddings", payload)
        return data["vectors"]

    def chat(
        self,
        user_id: int,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"messages": messages}
        if model:
            payload["model"] = model
        data = self._signed_post("/v1/chat", payload)
        return data


class LocalAiClient:
    def __init__(self) -> None:
        # Prefer OpenAI GPT-5-nano as primary, then OpenRouter as backup
        if getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY:
            self._provider = OpenAIProvider()
            # Initialize backup provider with OpenRouter if available
            self._backup_provider = OpenRouterProvider() if settings.OPENROUTER_KEY else None
        elif settings.OPENROUTER_KEY2:
            self._provider = OpenRouterBackupProvider()
            self._backup_provider = OpenRouterProvider() if settings.OPENROUTER_KEY else None
        elif settings.OPENROUTER_KEY:
            self._provider = OpenRouterProvider()
            self._backup_provider = None
        else:
            self._provider = OpenAIProvider()
            self._backup_provider = None

    def embeddings(
        self, user_id: int, texts: List[str], *, simulate: bool = False
    ) -> List[List[float]]:
        return [self._provider.embedding(t, simulate=simulate) for t in texts]

    def chat(
        self,
        user_id: int,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        # Try main provider first
        try:
            if hasattr(self._provider, "chat"):
                try:
                    return self._provider.chat(user_id, messages, simulate=simulate, model=model)  # type: ignore[arg-type]
                except TypeError:
                    pass
            return self._provider.chat(user_id, messages, simulate=simulate)
        except Exception as main_exc:
            # Check if it's a rate limit or similar error that should trigger fallback
            error_msg = str(main_exc).lower()
            is_rate_limit = any(keyword in error_msg for keyword in [
                "rate limit", "too many requests", "quota exceeded", 
                "429", "limit exceeded", "throttled"
            ])
            
            # If we have a backup provider and it's a rate limit error, try backup
            if self._backup_provider and is_rate_limit:
                try:
                    if hasattr(self._backup_provider, "chat"):
                        try:
                            return self._backup_provider.chat(user_id, messages, simulate=simulate, model=model)  # type: ignore[arg-type]
                        except TypeError:
                            pass
                    return self._backup_provider.chat(user_id, messages, simulate=simulate)
                except Exception as backup_exc:
                    # If backup also fails, raise the original error
                    raise main_exc from backup_exc
            
            # If no backup or not a rate limit error, raise the original error
            raise main_exc


_client: LocalAiClient | AiClient | None = None


def get_ai_client() -> LocalAiClient | AiClient:
    global _client
    if settings.AI_SERVICE_URL and settings.AI_INTERNAL_SECRET:
        if not isinstance(_client, AiClient):
            _client = AiClient(settings.AI_SERVICE_URL, settings.AI_INTERNAL_SECRET)
    else:
        if not isinstance(_client, LocalAiClient):
            _client = LocalAiClient()
    return _client
