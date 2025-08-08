from pydantic_settings import BaseSettings, SettingsConfigDict
# Para Pydantic 1.x descomenta las dos líneas siguientes
# from pydantic import BaseSettings
# from typing import Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlanifitAI"
    API_V1_STR: str = "/api/v1"
    OPENAI_API_KEY: str
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@db:5432/planifitai"
    )

    # Si vas a usar estas claves más adelante, las dejamos opcionales
    SECRET_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # ——— CONFIGURACIÓN Pydantic v2 ———
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",        # <— ¡IGNORA variables extra!
    )

    # ------------- Pydantic v1 -------------
    # class Config:
    #     env_file = ".env"
    #     extra = "ignore"      # <— también ‘ignore’

settings = Settings()
