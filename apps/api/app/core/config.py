"""Typed, process-wide infrastructure configuration."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
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

    upload_root: Path = Path("data/uploads")
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=1024 * 1024 * 1024)

    chunk_size_chars: int = Field(default=1200, ge=100, le=100_000)
    chunk_overlap_chars: int = Field(default=200, ge=0, le=99_999)

    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = Field(default="qwen3-embedding:0.6b", min_length=1, max_length=255)
    embedding_dimension: int = Field(default=1024, ge=1, le=65_536)
    embedding_batch_size: int = Field(default=32, ge=1, le=1024)
    embedding_request_timeout_seconds: float = Field(default=30.0, gt=0, le=600)

    chroma_host: str = Field(default="localhost", min_length=1, max_length=253)
    chroma_http_port: int = Field(default=8000, ge=1, le=65_535)
    chroma_ssl: bool = False
    chroma_collection_name: str = Field(
        default="agentforge_document_chunks",
        min_length=3,
        max_length=512,
        pattern=r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$",
    )

    ingestion_lease_seconds: int = Field(default=300, ge=30, le=86_400)
    ingestion_retry_delay_seconds: int = Field(default=30, ge=1, le=86_400)
    ingestion_worker_poll_interval_seconds: float = Field(default=2.0, gt=0, le=300)
    ingestion_rebuild_batch_size: int = Field(default=32, ge=1, le=1024)

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

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        """Require a bounded HTTP endpoint rather than an arbitrary URL scheme."""
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            msg = "OLLAMA_BASE_URL must be an http:// or https:// URL"
            raise ValueError(msg)
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            msg = "OLLAMA_BASE_URL must not contain credentials, a query, or a fragment"
            raise ValueError(msg)
        return value.rstrip("/")

    @field_validator("chroma_host")
    @classmethod
    def validate_chroma_host(cls, value: str) -> str:
        """Accept a host only; scheme and port are configured separately."""
        if "://" in value or "/" in value or any(character.isspace() for character in value):
            msg = "CHROMA_HOST must be a hostname without a scheme, path, or whitespace"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_chunking_window(self) -> "Settings":
        """Guarantee that deterministic chunking always advances."""
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            msg = "CHUNK_OVERLAP_CHARS must be smaller than CHUNK_SIZE_CHARS"
            raise ValueError(msg)
        return self

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
