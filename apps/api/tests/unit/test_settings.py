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
