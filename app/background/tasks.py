from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

import httpx

from app.ai_client import get_ai_client
from app.background.celery_app import celery_app


def _sign(secret: bytes, ts: str, body: bytes) -> str:
    return hmac.new(secret, f"{ts}.".encode() + body, hashlib.sha256).hexdigest()


def _safe_callback(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def _maybe_callback(url: str | None, data: dict) -> None:
    if not url or not _safe_callback(url):
        return
    ts = str(int(time.time()))
    body = json.dumps(data, separators=(",", ":")).encode()
    secret = (
        os.getenv("CELERY_WEBHOOK_SECRET")
        or os.getenv("AI_INTERNAL_SECRET")
        or ""
    ).encode()
    sig = _sign(secret, ts, body) if secret else ""
    headers = {
        "Content-Type": "application/json",
        "X-Timestamp": ts,
        "X-Internal-Signature": sig,
    }
    try:  # pragma: no cover - best effort
        httpx.post(url, content=body, headers=headers, timeout=10)
    except Exception:
        pass


@celery_app.task(
    bind=True,
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def chat_task(self, payload: dict):
    client = get_ai_client()
    try:
        result = client.chat(0, payload.get("messages", []), model=payload.get("model"))
    except Exception as exc:  # pragma: no cover - failure path
        _maybe_callback(
            payload.get("callback_url"),
            {
                "task_id": self.request.id,
                "state": "FAILURE",
                "error": str(exc),
                "finished_at": int(time.time()),
            },
        )
        raise
    _maybe_callback(
        payload.get("callback_url"),
        {
            "task_id": self.request.id,
            "state": "SUCCESS",
            "result": result,
            "finished_at": int(time.time()),
        },
    )
    return result


@celery_app.task(
    bind=True,
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def embeddings_task(self, payload: dict):
    client = get_ai_client()
    try:
        result = client.embeddings(0, payload.get("texts", []))
    except Exception as exc:  # pragma: no cover - failure path
        _maybe_callback(
            payload.get("callback_url"),
            {
                "task_id": self.request.id,
                "state": "FAILURE",
                "error": str(exc),
                "finished_at": int(time.time()),
            },
        )
        raise
    _maybe_callback(
        payload.get("callback_url"),
        {
            "task_id": self.request.id,
            "state": "SUCCESS",
            "result": result,
            "finished_at": int(time.time()),
        },
    )
    return result
