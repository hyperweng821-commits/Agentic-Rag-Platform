"""FastAPI dependency providers and request-scoped resources."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import async_session_maker
from app.ingestion.storage import LocalFileStorage
from app.services.knowledge_intake import KnowledgeIntakeService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one session per request, rolling back failed request work."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_app_settings() -> Settings:
    """Expose the cached settings object through FastAPI dependency injection."""
    return get_settings()


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]


def get_knowledge_intake_service(
    session: DatabaseSession,
    settings: AppSettings,
) -> KnowledgeIntakeService:
    """Build the request-scoped AF-1 service with its consumed local adapter."""
    return KnowledgeIntakeService(
        session,
        LocalFileStorage(settings.upload_root),
        max_upload_size_bytes=settings.max_upload_size_bytes,
    )


KnowledgeService = Annotated[KnowledgeIntakeService, Depends(get_knowledge_intake_service)]
