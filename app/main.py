# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.auth.routers import router as auth_router
from app.user_profile.routers import router as profile_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",     # ← mueve Swagger
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
    return app

app = create_app()