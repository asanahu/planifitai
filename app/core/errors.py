import os
from typing import Any, Mapping, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Flag de compatibilidad temporal
API_ENVELOPE_COMPAT = os.getenv("API_ENVELOPE_COMPAT", "false").lower() in {
    "1",
    "true",
    "yes",
}


class APIError(BaseModel):
    code: str
    http: int
    msg: str


# Códigos de dominio
AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
PLAN_NOT_FOUND = "PLAN_NOT_FOUND"
PLAN_INVALID_STATE = "PLAN_INVALID_STATE"
NUTRI_MEAL_NOT_FOUND = "NUTRI_MEAL_NOT_FOUND"

COMMON_VALIDATION = "COMMON_VALIDATION"
COMMON_INTEGRITY = "COMMON_INTEGRITY"
COMMON_HTTP = "COMMON_HTTP"
COMMON_UNEXPECTED = "COMMON_UNEXPECTED"


def ok(
    data: Any, http: int = 200, headers: Optional[Mapping[str, str]] = None
) -> JSONResponse:
    """Envuelve la respuesta exitosa bajo el sobre estándar."""
    payload = jsonable_encoder(data)
    headers = dict(headers or {})
    if API_ENVELOPE_COMPAT:
        _legacy = getattr(data, "__legacy__", False)
    return JSONResponse(
        status_code=http,
        content={"ok": True, "data": payload},
        headers=headers,
    )


def err(
    code: str,
    message: str,
    http: int = 400,
    headers: Optional[Mapping[str, str]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=http,
        content={"ok": False, "error": {"code": code, "message": message}},
        headers=headers or {},
    )
