from functools import lru_cache

from pydantic import Field, SecretStr
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

    # LLM explanations. Disabled by default: no external calls unless explicitly configured.
    # No model id is assumed — LLM_MODEL must be set to a model your account has access to.
    llm_provider: str = Field(default="disabled", pattern="^(disabled|anthropic|openai|gemini)$")
    llm_model: str | None = None
    llm_timeout_s: float = 30.0
    llm_max_output_tokens: int = 600
    llm_temperature: float = 0.2
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    # Prices change; enter the current list price per million tokens to get cost estimates.
    llm_price_input_per_mtok: float | None = None
    llm_price_output_per_mtok: float | None = None

    # RAG
    rag_store: str = Field(default="memory", pattern="^(memory|pgvector)$")
    rag_embedding_backend: str = Field(default="hashing", pattern="^(hashing|sentence_transformers)$")
    rag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_embedding_dim: int = 384  # must match knowledge_chunks.embedding column
    rag_top_k: int = 5
    rag_min_score: float = 0.2

    jwt_secret: str = "change-me-in-env"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
