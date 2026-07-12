"""Typed, process-wide infrastructure configuration."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported application runtime environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


def _find_env_file() -> Path:
    """Locate the repository-level .env file in local and container layouts."""
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env.example").is_file():
            return parent / ".env"
    return Path(".env")


class Settings(BaseSettings):
    """Validated settings for the backend foundation layer."""

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
        frozen=True,
        str_strip_whitespace=True,
    )

    app_name: str = "agentic-rag-backend"
    app_version: str = "0.1.0"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    docs_enabled: bool = True

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool | None = None

    database_url: str = (
        "postgresql+asyncpg://agentic_rag:agentic_rag_dev_only@localhost:5432/agentic_rag"
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)
    database_healthcheck_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Require the async PostgreSQL driver used by the application."""
        if not value.startswith("postgresql+asyncpg://"):
            msg = "DATABASE_URL must use the postgresql+asyncpg:// scheme"
            raise ValueError(msg)
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        """Reject wildcard CORS when credentials may be introduced later."""
        if not value:
            msg = "CORS_ORIGINS must contain at least one explicit origin"
            raise ValueError(msg)
        if "*" in value:
            msg = "CORS_ORIGINS must not contain a wildcard"
            raise ValueError(msg)
        return value

    @property
    def use_json_logs(self) -> bool:
        """Use explicit configuration or default to JSON in production."""
        if self.log_json is not None:
            return self.log_json
        return self.app_env is Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the single immutable settings instance for this process."""
    return Settings()
