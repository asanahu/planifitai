import logging
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette import status

from app.ai.routers import router as ai_router
from app.auth.routers import router as auth_router
from app.core.config import settings
from app.core.errors import (
    AUTH_FORBIDDEN,
    COMMON_HTTP,
    COMMON_INTEGRITY,
    COMMON_UNEXPECTED,
    COMMON_VALIDATION,
    NUTRI_MEAL_NOT_FOUND,
    PLAN_NOT_FOUND,
    err,
    ok,
)
from app.notifications.routers import router as notifications_router
from app.nutrition.routers import router as nutrition_router
from app.progress.routers import router as progress_router
from app.routers.ai_jobs import router as ai_jobs_router
from app.routers.training import router as training_router
from app.routers.users import router as users_router
from app.routines.routers import router as routines_router
from app.user_profile.routers import router as profile_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    @app.get("/health", include_in_schema=False)
    async def health():
        return ok({"status": "ok"})

    @app.get("/", include_in_schema=False)
    async def root():
        return ok({"message": "PlanifitAI API up"})

    # Estos routers NO llevan /api/v1 por dentro → se incluye con prefix global
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(profile_router, prefix=settings.API_V1_STR)
    app.include_router(users_router, prefix=settings.API_V1_STR)
    app.include_router(routines_router, prefix=settings.API_V1_STR)
    app.include_router(progress_router, prefix=settings.API_V1_STR)
    app.include_router(nutrition_router, prefix=settings.API_V1_STR)
    app.include_router(notifications_router, prefix=settings.API_V1_STR)
    if settings.AI_FEATURES_ENABLED:
        app.include_router(ai_router, prefix=settings.API_V1_STR)

    # 🔴 Importante: training_router ya tiene prefix="/api/v1/training"
    # Por eso se incluye SIN prefix extra para evitar /api/v1/api/v1/training
    app.include_router(training_router)

    # permitir llamadas desde el frontend durante desarrollo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # origen del servidor de Vite
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # (Este router ya gestiona sus propias rutas)
    app.include_router(ai_jobs_router)

    ERROR_MAP = {
        "Meal not found": NUTRI_MEAL_NOT_FOUND,
        "Routine not found": PLAN_NOT_FOUND,
        "Not authenticated": AUTH_FORBIDDEN,
        "Could not validate credentials": AUTH_FORBIDDEN,
        "Invalid token type for this operation": AUTH_FORBIDDEN,
    }

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return err(COMMON_VALIDATION, "Error de validación de la solicitud", http=422)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code = ERROR_MAP.get(str(exc.detail), COMMON_HTTP)
        if (
            exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
            and code == COMMON_HTTP
        ):
            code = AUTH_FORBIDDEN
        return err(code, str(exc.detail), http=exc.status_code)

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        return err(COMMON_INTEGRITY, "Conflicto de integridad", http=409)

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        return err(COMMON_UNEXPECTED, "Error interno inesperado", http=500)

    return app


app = create_app()
