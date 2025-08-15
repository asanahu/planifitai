"""Request signature verification."""

from __future__ import annotations

import hmac
import os
import time
from hashlib import sha256

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

SECRET = os.getenv("AI_INTERNAL_SECRET", "")
PAYLOAD_LIMIT = 256 * 1024  # 256 KB


class HMACMiddleware(BaseHTTPMiddleware):
    """Validate HMAC signature for internal requests."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/healthz", "/readyz"}:
            return await call_next(request)

        ts = request.headers.get("X-Timestamp")
        sig = request.headers.get("X-Internal-Signature")
        if not ts or not sig:
            return JSONResponse(
                status_code=401, content={"detail": "missing signature"}
            )

        try:
            ts_int = int(ts)
        except ValueError:  # pragma: no cover - defensive
            return JSONResponse(status_code=401, content={"detail": "bad timestamp"})

        now = int(time.time())
        if abs(now - ts_int) > 60:
            return JSONResponse(
                status_code=401, content={"detail": "timestamp out of range"}
            )

        body = await request.body()
        if len(body) > PAYLOAD_LIMIT:
            return JSONResponse(
                status_code=413, content={"detail": "payload too large"}
            )

        msg = f"{ts}.".encode() + body
        expected = hmac.new(SECRET.encode(), msg, sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return JSONResponse(
                status_code=401, content={"detail": "invalid signature"}
            )

        # Re-inject body so downstream handlers can read it again
        request._body = body
        return await call_next(request)
