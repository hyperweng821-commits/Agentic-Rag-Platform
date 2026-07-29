"""Shared opt-in PostgreSQL infrastructure for integration tests."""

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db.base import Base

INTEGRATION_DATABASE_URL_ENV = "AF2A_TEST_DATABASE_URL"


def require_integration_database_url() -> str:
    """Resolve explicit live infrastructure or stop with environment-aware policy."""
    database_url = os.getenv(INTEGRATION_DATABASE_URL_ENV)
    if database_url is None or not database_url.strip():
        message = f"{INTEGRATION_DATABASE_URL_ENV} is not configured"
        if os.getenv("CI", "").strip().lower() == "true":
            pytest.fail(message)
        pytest.skip(message)
    if not database_url.startswith("postgresql+asyncpg://"):
        pytest.fail(f"{INTEGRATION_DATABASE_URL_ENV} must use postgresql+asyncpg://")
    return database_url


@pytest.fixture(scope="session")
def integration_database_url() -> str:
    """Require explicit live infrastructure in CI while allowing local opt-in."""
    return require_integration_database_url()


@pytest.fixture
async def postgres_sessions(
    integration_database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Create all current models in one isolated PostgreSQL schema."""
    schema_name = f"agentforge_test_{uuid4().hex}"
    admin_engine = create_async_engine(integration_database_url, poolclass=NullPool)
    test_engine = create_async_engine(
        integration_database_url,
        connect_args={"server_settings": {"search_path": schema_name}},
        poolclass=NullPool,
    )
    schema_created = False
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(CreateSchema(schema_name))
        schema_created = True
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    finally:
        await test_engine.dispose()
        if schema_created:
            async with admin_engine.begin() as connection:
                await connection.execute(DropSchema(schema_name, cascade=True, if_exists=True))
        await admin_engine.dispose()


@pytest.fixture
async def postgres_migration_engine(
    integration_database_url: str,
) -> AsyncIterator[AsyncEngine]:
    """Create an empty isolated schema for real Alembic operations."""
    schema_name = f"agentforge_migration_{uuid4().hex}"
    admin_engine = create_async_engine(integration_database_url, poolclass=NullPool)
    test_engine = create_async_engine(
        integration_database_url,
        connect_args={"server_settings": {"search_path": schema_name}},
        poolclass=NullPool,
    )
    schema_created = False
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(CreateSchema(schema_name))
        schema_created = True
        yield test_engine
    finally:
        await test_engine.dispose()
        if schema_created:
            async with admin_engine.begin() as connection:
                await connection.execute(DropSchema(schema_name, cascade=True, if_exists=True))
        await admin_engine.dispose()
