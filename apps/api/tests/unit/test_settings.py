"""Tests for settings validation and process-wide caching."""

import pytest
from pydantic import ValidationError

from app.core.config import Environment, Settings, get_settings


def test_settings_are_cached_once_per_process() -> None:
    assert get_settings() is get_settings()


def test_settings_reject_non_async_postgresql_url() -> None:
    with pytest.raises(ValidationError, match="postgresql\\+asyncpg"):
        Settings(_env_file=None, database_url="postgresql://localhost/agentic_rag")


def test_settings_reject_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        Settings(_env_file=None, cors_origins=["*"])


def test_settings_reject_chunk_overlap_that_cannot_advance() -> None:
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP_CHARS"):
        Settings(_env_file=None, chunk_size_chars=100, chunk_overlap_chars=100)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("ollama_base_url", "file:///private/model", "OLLAMA_BASE_URL"),
        ("ollama_base_url", "https://user:secret@example.test", "credentials"),
        ("chroma_host", "http://chroma:8000", "CHROMA_HOST"),
        ("chroma_host", "chroma/internal", "CHROMA_HOST"),
    ],
)
def test_settings_reject_unsafe_provider_locations(
    field: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None, **{field: value})


def test_settings_normalize_ollama_base_url() -> None:
    settings = Settings(_env_file=None, ollama_base_url="http://localhost:11434/")

    assert settings.ollama_base_url == "http://localhost:11434"


@pytest.mark.parametrize(
    "collection_name",
    ["UPPERCASE", "-leading-dash", "trailing-dot.", "ab"],
)
def test_settings_reject_invalid_chroma_collection_names(collection_name: str) -> None:
    with pytest.raises(ValidationError, match="chroma_collection_name"):
        Settings(_env_file=None, chroma_collection_name=collection_name)


def test_production_defaults_to_json_logs() -> None:
    settings = Settings(
        _env_file=None,
        app_env=Environment.PRODUCTION,
        log_json=None,
    )

    assert settings.use_json_logs is True


def test_explicit_log_format_overrides_environment() -> None:
    settings = Settings(
        _env_file=None,
        app_env=Environment.PRODUCTION,
        log_json=False,
    )

    assert settings.use_json_logs is False
