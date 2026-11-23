from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration. See /.env.example for all variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DermaCare API"
    environment: str = Field(default="development", pattern="^(development|test|staging|production)$")
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://dermacare:dermacare@localhost:5432/dermacare"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Analysis: "mock" until trained models are registered.
    analysis_backend: str = Field(default="mock", pattern="^(mock|torch)$")
    max_upload_mb: int = 8

    # LLM explanations (RAG). Disabled by default — no paid calls unless explicitly configured.
    llm_provider: str = Field(default="disabled", pattern="^(disabled|anthropic|openai|local)$")
    llm_model: str | None = None
    llm_api_key: str | None = None

    jwt_secret: str = "change-me-in-env"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
