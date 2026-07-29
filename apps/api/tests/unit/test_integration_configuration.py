"""Tests for the centralized live PostgreSQL requirement."""

import pytest
from tests.integration.conftest import (
    INTEGRATION_DATABASE_URL_ENV,
    require_integration_database_url,
)


def test_missing_integration_database_is_a_hard_failure_in_ci(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(INTEGRATION_DATABASE_URL_ENV, raising=False)
    monkeypatch.setenv("CI", "true")

    with pytest.raises(pytest.fail.Exception, match=INTEGRATION_DATABASE_URL_ENV):
        require_integration_database_url()


def test_missing_integration_database_remains_an_intentional_local_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(INTEGRATION_DATABASE_URL_ENV, raising=False)
    monkeypatch.delenv("CI", raising=False)

    with pytest.raises(pytest.skip.Exception, match=INTEGRATION_DATABASE_URL_ENV):
        require_integration_database_url()


def test_integration_database_requires_async_postgresql_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        INTEGRATION_DATABASE_URL_ENV,
        "postgresql://test@127.0.0.1/test",
    )

    with pytest.raises(pytest.fail.Exception, match=r"postgresql\+asyncpg"):
        require_integration_database_url()
