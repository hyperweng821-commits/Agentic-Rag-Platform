"""Tests for request-scoped session cleanup and application shutdown."""

from types import TracebackType
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.dependencies as dependencies
import app.db.session as session_module
import app.main as main_module
from app.db.base import NAMING_CONVENTION, Base


class FakeSessionContext:
    """Minimal async context matching the behavior used by async_sessionmaker."""

    def __init__(self) -> None:
        self.session = AsyncMock(spec=AsyncSession)
        self.session.in_transaction.return_value = False

    async def __aenter__(self) -> AsyncSession:
        return cast(AsyncSession, self.session)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.session.close()


def test_declarative_base_uses_stable_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


async def test_database_dependency_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = FakeSessionContext()
    monkeypatch.setattr(dependencies, "async_session_maker", lambda: context)
    generator = dependencies.get_db_session()

    yielded_session = await anext(generator)
    await generator.aclose()

    assert yielded_session is context.session
    context.session.rollback.assert_not_awaited()
    context.session.close.assert_awaited_once()


async def test_database_dependency_rolls_back_after_request_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = FakeSessionContext()
    context.session.in_transaction.return_value = True
    monkeypatch.setattr(dependencies, "async_session_maker", lambda: context)
    generator = dependencies.get_db_session()
    await anext(generator)

    with pytest.raises(RuntimeError, match="request failed"):
        await generator.athrow(RuntimeError("request failed"))

    context.session.rollback.assert_awaited_once()
    context.session.close.assert_awaited_once()


async def test_lifespan_disposes_database_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispose_engine = AsyncMock()
    monkeypatch.setattr(main_module, "dispose_engine", dispose_engine)
    application = main_module.create_app()

    async with main_module.lifespan(application):
        assert dispose_engine.await_count == 0

    dispose_engine.assert_awaited_once_with()


async def test_dispose_engine_closes_connection_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = AsyncMock()
    monkeypatch.setattr(session_module, "engine", engine)

    await session_module.dispose_engine()

    engine.dispose.assert_awaited_once_with()
