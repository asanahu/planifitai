# app/main.py
import logging
import traceback

import sqlalchemy
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai.routers import router as ai_router
from app.auth.routers import router as auth_router
from app.core.config import settings
from app.core.errors import (
    AUTH_FORBIDDEN,
    COMMON_HTTP,
    COMMON_INTEGRITY,
    COMMON_UNEXPECTED,
    COMMON_VALIDATION,
    ERROR_MAP,
    err,
)
from app.notifications.routers import router as notifications_router
from app.nutrition.routers import router as nutrition_router
from app.progress.routers import router as progress_router
from app.routers.ai_jobs import router as ai_jobs_router
from app.routines.routers import router as routines_router
from app.user_profile.routers import router as profile_router

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",  # ← mueve Swagger
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # Rutas
    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "PlanifitAI API up"}

    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(profile_router, prefix=settings.API_V1_STR)
    app.include_router(routines_router, prefix=settings.API_V1_STR)
    app.include_router(progress_router, prefix=settings.API_V1_STR)
    app.include_router(nutrition_router, prefix=settings.API_V1_STR)
    app.include_router(notifications_router, prefix=settings.API_V1_STR)
    app.include_router(ai_router, prefix=settings.API_V1_STR)
    app.include_router(ai_jobs_router)

    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return err(COMMON_VALIDATION, str(exc), 422)

    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        code = ERROR_MAP.get(exc.detail, COMMON_HTTP)
        if exc.status_code in (401, 403) and code == COMMON_HTTP:
            code = AUTH_FORBIDDEN
        return err(code, exc.detail, exc.status_code)

    async def integrity_error_handler(
        request: Request, exc: sqlalchemy.exc.IntegrityError
    ) -> JSONResponse:
        return err(COMMON_INTEGRITY, "Integrity error", 409)

    async def unexpected_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        traceback.print_exc()
        return err(COMMON_UNEXPECTED, "Unexpected error", 500)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(sqlalchemy.exc.IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
    return app


app = create_app()
