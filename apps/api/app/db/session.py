"""Async PostgreSQL engine and session-factory configuration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout_seconds,
    pool_recycle=settings.database_pool_recycle_seconds,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def check_database_connection(session: AsyncSession) -> None:
    """Run a minimal query that proves the current database session is usable."""
    await session.execute(text("SELECT 1"))


async def dispose_engine() -> None:
    """Close all pooled connections during application shutdown."""
    await engine.dispose()
