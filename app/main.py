from fastapi import FastAPI
from app.core.config import settings

# Routers se importarán cuando existan.

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")
    return app

app = create_app()