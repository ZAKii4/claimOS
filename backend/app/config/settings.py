"""
Application settings loaded from environment variables.

Uses pydantic-settings to provide typed, validated configuration
with sensible defaults for local development.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # -- Application ----------------------------------------------------------
    PROJECT_NAME: str = "claimOS API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # -- Security ---------------------------------------------------------------
    # No hardcoded default: an empty value here means the JWT signing key is
    # generated fresh per-process (see app/security/jwt_manager.py), which is
    # fine for local dev but invalidates all tokens on restart. Production
    # deployments MUST set SECRET_KEY explicitly.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"

    # -- Database -------------------------------------------------------------
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:secure_postgres_password_123@localhost:5433/claimos_db")

    # -- API ------------------------------------------------------------------
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # -- File Storage ---------------------------------------------------------
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # -- OCR --------------------------------------------------------------------
    # Tesseract traineddata codes, "+"-joined. Insurance documents in this
    # market are French, with Arabic on national ID / official documents —
    # both traineddata packs must be installed (`tesseract --list-langs`).
    OCR_LANGUAGES: str = os.getenv("OCR_LANGUAGES", "fra+ara+eng")

    # -- Virus Scanning ---------------------------------------------------------
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "localhost")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))

    # -- LLM Config -----------------------------------------------------------
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5")

    # Per-agent model routing for the 6-agent claim collaboration pipeline
    # (app/agents/modules/) — deliberately separate settings keys, not a
    # single shared default, so each agent's model can be tuned independently
    # as hardware/quality tradeoffs change, without touching agent code. All
    # three currently default to the same small model (qwen3:4b, ~2.5GB) —
    # see docs/COURS_08_LANGGRAPH_ET_MODELES.md for the research and the
    # real disk-space constraint that shaped this choice.
    OLLAMA_FRAUD_MODEL: str = os.getenv("OLLAMA_FRAUD_MODEL", "qwen3:4b")
    OLLAMA_LEGAL_MODEL: str = os.getenv("OLLAMA_LEGAL_MODEL", "qwen3:4b")
    OLLAMA_DECISION_MODEL: str = os.getenv("OLLAMA_DECISION_MODEL", "qwen3:4b")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY", None)
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY", None)



@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
