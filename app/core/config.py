from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlanifitAI"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Opcionales (si los usas después)
    OPENAI_EMBEDDING_MODEL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()