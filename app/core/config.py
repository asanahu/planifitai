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
    FORCE_SIMULATE_MODE: bool = Field(default=False)  # Usar IA real

    # Nutrition data sources
    FOOD_SOURCE: str = Field(default="openfoodfacts")
    FDC_API_KEY: str | None = None

    # Opcionales (si los usas después)
    API_OPEN_AI: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str | None = None
    OPENAI_MAX_TOKENS: int = 1500
    OPENAI_TEMPERATURE: float = 0.4
    OPENAI_TIMEOUT_S: int = 120
    OPENAI_RETRIES: int = 2
    AI_RESPONSE_JSON_STRICT: bool = True
    AI_DAILY_BUDGET_CENTS: int = 100
    AI_SERVICE_URL: str | None = None
    AI_INTERNAL_SECRET: str | None = None

    # OpenRouter (DeepSeek free)
    OPENROUTER_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_CHAT_MODEL: str = "deepseek/deepseek-chat-v3.1:free"
    # Optional headers for OpenRouter rankings (no funcional, solo ranking)
    OPENROUTER_HTTP_REFERER: str | None = None
    OPENROUTER_APP_TITLE: str | None = None
    
    # OpenRouter Backup (GLM-4.5 Air free)
    OPENROUTER_KEY2: str | None = None
    OPENROUTER_BACKUP_CHAT_MODEL: str = "z-ai/glm-4.5-air:free"

    # Wger API
    WGER_API_TOKEN: str | None = None

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
