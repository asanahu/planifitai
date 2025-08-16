from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from prometheus_client import CollectorRegistry, Histogram, generate_latest
from starlette.responses import PlainTextResponse

from .provider import OpenAIProvider
from .schemas import ChatRequest, ChatResponse, EmbeddingsRequest, EmbeddingsResponse
from .security import HMACMiddleware

log = logging.getLogger("ai_service")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(handler)
log.setLevel(logging.INFO)

METRIC_REGISTRY = CollectorRegistry()
REQUEST_LATENCY = Histogram(
    "ai_request_latency_ms", "Request latency", ["endpoint"], registry=METRIC_REGISTRY
)

app = FastAPI()
app.add_middleware(HMACMiddleware)

provider = OpenAIProvider()


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration_ms / 1000)
    log.info(
        json.dumps(
            {
                "request_id": request_id,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict:
    try:
        provider.chat(0, [], simulate=True)
        status = "ok"
    except Exception:  # pragma: no cover - defensive
        status = "degraded"
    return {"status": status}


@app.post("/v1/embeddings", response_model=EmbeddingsResponse)
async def embeddings(req: EmbeddingsRequest) -> EmbeddingsResponse:
    vectors = [provider.embedding(t, simulate=True) for t in req.texts]
    return EmbeddingsResponse(vectors=vectors)


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    resp = provider.chat(0, [m.model_dump() for m in req.messages], simulate=True)
    return ChatResponse(reply=resp["reply"], usage=resp.get("usage", {}))


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    data = generate_latest(METRIC_REGISTRY).decode()
    return PlainTextResponse(data, media_type="text/plain")
