# app/main.py
import logging

from fastapi import FastAPI

from app.ai.routers import router as ai_router
from app.auth.routers import router as auth_router
from app.core.config import settings
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
    return app


app = create_app()
