from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlanifitAI"
    API_V1_STR: str = "/api/v1"
    OPENAI_API_KEY: str
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/planifitai"

    class Config:
        env_file = ".env"

settings = Settings()