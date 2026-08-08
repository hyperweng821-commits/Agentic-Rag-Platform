"""Tests for settings validation and process-wide caching."""

from uuid import UUID

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


def test_settings_accept_trusted_chroma_collection_uuid_and_bounded_retrieval_timeout() -> None:
    collection_uuid = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    settings = Settings(
        _env_file=None,
        chroma_collection_uuid=collection_uuid,
        chroma_retrieval_timeout_seconds=600,
    )

    assert settings.chroma_collection_uuid == collection_uuid
    assert settings.chroma_retrieval_timeout_seconds == 600


@pytest.mark.parametrize(
    "collection_uuid",
    [
        "aaaaaaaaaaaa4aaa8aaaaaaaaaaaaaaa",
        "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
        "{aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa}",
        "urn:uuid:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    ],
)
def test_settings_reject_noncanonical_chroma_collection_uuid(
    collection_uuid: str,
) -> None:
    with pytest.raises(ValidationError, match="canonical UUID"):
        Settings(_env_file=None, chroma_collection_uuid=collection_uuid)


def test_settings_accept_canonical_chroma_collection_uuid_text() -> None:
    canonical = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    settings = Settings(_env_file=None, chroma_collection_uuid=canonical)

    assert settings.chroma_collection_uuid == UUID(canonical)


@pytest.mark.parametrize("timeout", [0, 601])
def test_settings_reject_unbounded_chroma_retrieval_timeout(timeout: float) -> None:
    with pytest.raises(ValidationError, match="chroma_retrieval_timeout_seconds"):
        Settings(_env_file=None, chroma_retrieval_timeout_seconds=timeout)


def test_production_defaults_to_json_logs() -> None:
    settings = Settings(
        _env_file=None,
        app_env=Environment.PRODUCTION,
        log_json=None,
        session_cookie_secure=True,
    )

    assert settings.use_json_logs is True


def test_explicit_log_format_overrides_environment() -> None:
    settings = Settings(
        _env_file=None,
        app_env=Environment.PRODUCTION,
        log_json=False,
        session_cookie_secure=True,
    )

    assert settings.use_json_logs is False


def test_authentication_settings_have_bounded_secure_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.session_ttl_seconds == 28_800
    assert settings.session_cookie_name == "agentforge_session"
    assert settings.csrf_cookie_name == "agentforge_csrf"
    assert settings.session_cookie_samesite == "strict"


def test_settings_reject_identical_session_and_csrf_cookie_names() -> None:
    with pytest.raises(ValidationError, match="must be different"):
        Settings(
            _env_file=None,
            session_cookie_name="same_cookie",
            csrf_cookie_name="same_cookie",
        )


def test_production_requires_secure_session_cookies() -> None:
    with pytest.raises(ValidationError, match="SESSION_COOKIE_SECURE"):
        Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            session_cookie_secure=False,
        )


def test_production_rejects_debug_before_application_startup() -> None:
    with pytest.raises(ValidationError, match="APP_DEBUG"):
        Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            app_debug=True,
            session_cookie_secure=True,
        )


@pytest.mark.parametrize("environment", [Environment.DEVELOPMENT, Environment.TEST])
def test_non_production_environments_allow_explicit_debug(environment: Environment) -> None:
    settings = Settings(_env_file=None, app_env=environment, app_debug=True)

    assert settings.app_debug is True


def test_sensitive_settings_inputs_are_hidden_from_validation_errors() -> None:
    sentinel = "".join(("settings-", "credential-sentinel"))
    invalid_database_url = f"postgresql://user:{sentinel}@database.example/app"

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, database_url=invalid_database_url)

    rendered = str(exc_info.value)
    assert "postgresql+asyncpg" in rendered
    assert sentinel not in rendered
    assert invalid_database_url not in rendered

    invalid_provider_url = f"https://user:{sentinel}@provider.example"
    with pytest.raises(ValidationError) as provider_exc_info:
        Settings(_env_file=None, ollama_base_url=invalid_provider_url)

    provider_rendered = str(provider_exc_info.value)
    assert "credentials" in provider_rendered
    assert sentinel not in provider_rendered
    assert invalid_provider_url not in provider_rendered


@pytest.mark.parametrize("max_concurrency", [0, 9])
def test_argon2_concurrency_setting_is_bounded(max_concurrency: int) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, argon2_max_concurrency=max_concurrency)


def test_argon2_concurrency_has_safe_default() -> None:
    assert Settings(_env_file=None).argon2_max_concurrency == 2
