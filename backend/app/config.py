"""
DeviationIQ — Application Configuration

All secrets from environment variables; never hardcoded (SC-01 from Security Plan).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql+asyncpg://aivoa:aivoa_dev_password@localhost:5432/aivoa_db"
    # Synchronous URL for Alembic migrations
    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")

    # --- Groq ---
    groq_api_key: str = ""
    groq_model_large: str = "openai/gpt-oss-120b"
    groq_model_small: str = "openai/gpt-oss-20b"

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- PostgreSQL (for docker-compose healthcheck reference) ---
    postgres_user: str = "aivoa"
    postgres_password: str = "aivoa_dev_password"
    postgres_db: str = "aivoa_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- Security & JWT (21 CFR Part 11) ---
    jwt_secret: str = "deviationiq-enterprise-secure-jwt-secret-key-2026-xyz"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480  # 8-hour clinical shift duration

    # --- Traffic & Overload Protection ---
    rate_limit_per_minute: int = 200            # General endpoints
    rate_limit_auth_per_minute: int = 15        # Brute-force protection
    rate_limit_ai_per_minute: int = 40          # AI triage burst gate
    max_request_body_bytes: int = 26214400      # 25 MB max payload ceiling
    llm_concurrency_limit: int = 5              # Max concurrent Groq LLM invocations

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
