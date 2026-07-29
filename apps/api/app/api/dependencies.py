"""FastAPI dependency providers and request-scoped resources."""

import hmac
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import async_session_maker
from app.ingestion.storage import LocalFileStorage
from app.security import AuthenticationService, CsrfError, PasswordWorkLimiter, Principal
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


def get_authentication_service(
    request: Request,
    session: DatabaseSession,
    settings: AppSettings,
) -> AuthenticationService:
    """Build the request-scoped opaque-session authentication service."""
    return AuthenticationService(
        session,
        session_ttl=timedelta(seconds=settings.session_ttl_seconds),
        password_work_limiter=cast(
            PasswordWorkLimiter,
            request.app.state.password_work_limiter,
        ),
    )


Authentication = Annotated[AuthenticationService, Depends(get_authentication_service)]


async def get_current_principal(
    request: Request,
    authentication: Authentication,
    settings: AppSettings,
) -> Principal:
    """Authenticate the opaque session cookie and return its stable principal."""
    return await authentication.authenticate_session(
        request.cookies.get(settings.session_cookie_name)
    )


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


async def get_csrf_protected_principal(
    request: Request,
    principal: CurrentPrincipal,
    authentication: Authentication,
    settings: AppSettings,
) -> Principal:
    """Require double-submit CSRF proof bound to the authenticated session."""
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")
    if (
        csrf_cookie is None
        or csrf_header is None
        or not hmac.compare_digest(
            csrf_cookie.encode("utf-8"),
            csrf_header.encode("utf-8"),
        )
    ):
        raise CsrfError
    await authentication.validate_csrf(
        session_token=request.cookies.get(settings.session_cookie_name),
        csrf_token=csrf_header,
    )
    return principal


CsrfProtectedPrincipal = Annotated[Principal, Depends(get_csrf_protected_principal)]


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
