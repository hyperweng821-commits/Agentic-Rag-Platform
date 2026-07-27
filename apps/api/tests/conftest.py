"""Shared backend fixtures with all external infrastructure isolated."""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

TEST_ENVIRONMENT = {
    "APP_NAME": "agentic-rag-backend",
    "APP_VERSION": "0.1.0",
    "APP_ENV": "test",
    "APP_DEBUG": "false",
    "DOCS_ENABLED": "true",
    "LOG_LEVEL": "INFO",
    "LOG_JSON": "false",
    "DATABASE_URL": "postgresql+asyncpg://test@127.0.0.1:65432/test_database",
    "DATABASE_ECHO": "false",
    "DATABASE_POOL_SIZE": "5",
    "DATABASE_MAX_OVERFLOW": "10",
    "DATABASE_POOL_TIMEOUT_SECONDS": "30",
    "DATABASE_POOL_RECYCLE_SECONDS": "1800",
    "DATABASE_HEALTHCHECK_TIMEOUT_SECONDS": "2",
    "UPLOAD_ROOT": str(Path.cwd().parent / "agentforge-test-uploads"),
    "MAX_UPLOAD_SIZE_BYTES": "10485760",
    "CORS_ORIGINS": '["http://localhost:3000","http://localhost:5173"]',
}
_ENV_FILE_NOT_CAPTURED = object()
_original_env_file: object = _ENV_FILE_NOT_CAPTURED


def pytest_configure(config: pytest.Config) -> None:
    """Pin settings and disable developer dotenv loading before test collection."""
    global _original_env_file

    os.environ.update(TEST_ENVIRONMENT)
    from app.core.config import Settings, get_settings

    if _original_env_file is _ENV_FILE_NOT_CAPTURED:
        _original_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore the Settings class after the pytest process finishes."""
    from app.core.config import Settings, get_settings

    if _original_env_file is not _ENV_FILE_NOT_CAPTURED:
        Settings.model_config["env_file"] = _original_env_file
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Reset cached settings and pin every test to controlled environment values."""
    from app.core.config import get_settings

    for name, value in TEST_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.fixture
def application() -> Iterator[FastAPI]:
    """Create an isolated application and clear dependency overrides afterwards."""
    from app.main import create_app

    test_application = create_app()
    yield test_application
    test_application.dependency_overrides.clear()


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[AsyncClient]:
    """Serve the ASGI app in-process without opening network sockets."""
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture
def database_session(application: FastAPI) -> AsyncMock:
    """Override the request session with a PostgreSQL-free async mock."""
    from app.api.dependencies import get_db_session

    session = AsyncMock(spec=AsyncSession)

    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield session

    application.dependency_overrides[get_db_session] = override_database_session
    return session
