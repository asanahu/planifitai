from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PlanifitAI"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # PHI encryption
    PHI_ENCRYPTION_KEY: str
    PHI_PROVIDER: str = "app"

    # Feature flags
    AI_FEATURES_ENABLED: bool = Field(default=False)

    # Nutrition data sources
    FOOD_SOURCE: str = Field(default="fdc")
    FDC_API_KEY: str | None = None

    # Opcionales (si los usas después)
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str | None = None
    OPENAI_MAX_TOKENS: int = 1500
    OPENAI_TEMPERATURE: float = 0.4
    OPENAI_TIMEOUT_S: int = 30
    OPENAI_RETRIES: int = 2
    AI_RESPONSE_JSON_STRICT: bool = True
    AI_DAILY_BUDGET_CENTS: int = 100
    AI_SERVICE_URL: str | None = None
    AI_INTERNAL_SECRET: str | None = None

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
