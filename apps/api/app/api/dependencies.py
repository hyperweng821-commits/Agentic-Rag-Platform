"""FastAPI dependency providers and request-scoped resources."""

import hmac
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import RetrievalServiceUnavailableError
from app.core.config import Settings, get_settings
from app.db.session import async_session_maker
from app.ingestion.embeddings import OllamaEmbeddingModel
from app.ingestion.storage import LocalFileStorage
from app.retrieval import (
    ChromaDenseRetrievalAdapter,
    FinalCandidateValidatorLoader,
    HybridRetrievalService,
    PostgresFinalAuthoritativeLoader,
    PostgresRetrievalAccess,
    ScopedKeywordRetrievalService,
)
from app.security import AuthenticationService, CsrfError, PasswordWorkLimiter, Principal
from app.security.authentication import SessionAuthenticationProof
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


async def get_csrf_protected_authentication_proof(
    request: Request,
    authentication: Authentication,
    settings: AppSettings,
) -> SessionAuthenticationProof:
    """Authenticate once and return the internal proof after CSRF validation."""
    session_token = request.cookies.get(settings.session_cookie_name)
    proof = await authentication.authenticate_session_with_proof(session_token)
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
        session_token=session_token,
        csrf_token=csrf_header,
    )
    return proof


CsrfProtectedAuthenticationProof = Annotated[
    SessionAuthenticationProof,
    Depends(get_csrf_protected_authentication_proof),
]


async def get_hybrid_retrieval_service(
    proof: CsrfProtectedAuthenticationProof,
    settings: AppSettings,
) -> AsyncGenerator[HybridRetrievalService, None]:
    """Compose and release one request-scoped Hybrid Retrieval service."""
    if settings.chroma_collection_uuid is None:
        raise RetrievalServiceUnavailableError

    embedding = OllamaEmbeddingModel(
        base_url=settings.ollama_base_url,
        model_id=settings.ollama_embed_model,
        dimension=settings.embedding_dimension,
        batch_size=settings.embedding_batch_size,
        timeout_seconds=settings.embedding_request_timeout_seconds,
    )
    dense: ChromaDenseRetrievalAdapter | None = None
    try:
        dense = ChromaDenseRetrievalAdapter(
            host=settings.chroma_host,
            http_port=settings.chroma_http_port,
            ssl=settings.chroma_ssl,
            collection_uuid=settings.chroma_collection_uuid,
            timeout_seconds=settings.chroma_retrieval_timeout_seconds,
        )
        yield HybridRetrievalService(
            keyword_service=ScopedKeywordRetrievalService(
                PostgresRetrievalAccess(async_session_maker)
            ),
            embedding_model=embedding,
            dense_retrieval=dense,
            final_validator=FinalCandidateValidatorLoader(
                PostgresFinalAuthoritativeLoader(async_session_maker)
            ),
        )
    finally:
        try:
            await embedding.close()
        finally:
            if dense is not None:
                await dense.close()


HybridRetrieval = Annotated[HybridRetrievalService, Depends(get_hybrid_retrieval_service)]


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
