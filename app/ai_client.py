"""Client for the external AI microservice with local fallback."""

from __future__ import annotations

import hmac
import json
import time
import uuid
from hashlib import sha256
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.ai.provider import OpenAIProvider


class AiClient:
    def __init__(
        self, base_url: str, secret: str, timeout: int = 10, max_retries: int = 2
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret = secret.encode()
        self._max_retries = max_retries
        self._client = httpx.Client(timeout=httpx.Timeout(timeout, connect=3, read=30))
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
        self._provider = OpenAIProvider()

    def embeddings(
        self, user_id: int, texts: List[str], *, simulate: bool = False
    ) -> List[List[float]]:
        return [self._provider.embedding(t, simulate=True) for t in texts]

    def chat(
        self,
        user_id: int,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        return self._provider.chat(user_id, messages, simulate=True)


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
