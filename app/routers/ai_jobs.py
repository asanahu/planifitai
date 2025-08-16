from __future__ import annotations

import json
import os

import redis
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request

from app.background.celery_app import celery_app
from app.background.tasks import chat_task, embeddings_task

router = APIRouter(prefix="/api/v1/ai/jobs", tags=["ai-jobs"])

_idem_ttl = 86400
_r = redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))


def _idem_key(key: str) -> str:
    return f"idem:{key}"


async def _read_payload(req: Request) -> dict:
    body = await req.body()
    if len(body) > 256 * 1024:
        raise HTTPException(status_code=413, detail="payload too large")
    try:
        payload = json.loads(body)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="invalid json") from exc
    return payload


@router.post("/chat", status_code=202)
async def create_chat_job(req: Request):
    payload = await _read_payload(req)
    messages = payload.get("messages") or []
    if len(messages) > 50:
        raise HTTPException(status_code=400, detail="too many messages")
    idem = req.headers.get("Idempotency-Key")
    if idem and (tid := _r.get(_idem_key(idem))):
        tid_s = tid.decode()
        return {"task_id": tid_s, "status_url": f"/api/v1/ai/jobs/{tid_s}"}
    task = chat_task.apply_async(kwargs={"payload": payload})
    if idem:
        _r.setex(_idem_key(idem), _idem_ttl, task.id)
    return {"task_id": task.id, "status_url": f"/api/v1/ai/jobs/{task.id}"}


@router.post("/embeddings", status_code=202)
async def create_embeddings_job(req: Request):
    payload = await _read_payload(req)
    texts = payload.get("texts") or []
    if len(texts) > 64:
        raise HTTPException(status_code=400, detail="too many texts")
    idem = req.headers.get("Idempotency-Key")
    if idem and (tid := _r.get(_idem_key(idem))):
        tid_s = tid.decode()
        return {"task_id": tid_s, "status_url": f"/api/v1/ai/jobs/{tid_s}"}
    task = embeddings_task.apply_async(kwargs={"payload": payload})
    if idem:
        _r.setex(_idem_key(idem), _idem_ttl, task.id)
    return {"task_id": task.id, "status_url": f"/api/v1/ai/jobs/{task.id}"}


@router.get("/{task_id}")
async def job_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    out = {"state": res.state}
    if res.state == "SUCCESS":
        out["result"] = res.result
    elif res.failed():
        out["error"] = str(res.result)
    return out
