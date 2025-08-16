from dataclasses import dataclass
from typing import Any, Dict

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


@dataclass
class APIError:
    code: str
    http: int
    msg: str


def ok(data: Any, http: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=http, content={"ok": True, "data": jsonable_encoder(data)}
    )


def err(code: str, message: str, http: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http,
        content={
            "ok": False,
            "error": {"code": code, "message": jsonable_encoder(message)},
        },
    )


# Error code constants
AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
PLAN_NOT_FOUND = "PLAN_NOT_FOUND"
PLAN_INVALID_STATE = "PLAN_INVALID_STATE"
NUTRI_MEAL_NOT_FOUND = "NUTRI_MEAL_NOT_FOUND"
COMMON_VALIDATION = "COMMON_VALIDATION"
COMMON_INTEGRITY = "COMMON_INTEGRITY"
COMMON_HTTP = "COMMON_HTTP"
COMMON_UNEXPECTED = "COMMON_UNEXPECTED"


# Optional map from common exception messages to error codes
ERROR_MAP: Dict[str, str] = {
    "Meal not found": NUTRI_MEAL_NOT_FOUND,
    "Routine not found": PLAN_NOT_FOUND,
    "Not authenticated": AUTH_FORBIDDEN,
    "Could not validate credentials": AUTH_FORBIDDEN,
}
