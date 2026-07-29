"""FastAPI application factory and process entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.cache_control import private_response_cache_control_middleware
from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_context_middleware
from app.db.session import dispose_engine
from app.security import PasswordWorkLimiter

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Log process lifecycle and release the SQLAlchemy connection pool."""
    settings = get_settings()
    logger.info(
        "application_started",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env.value,
    )
    try:
        yield
    finally:
        await dispose_engine()
        application.state.password_work_limiter.shutdown()
        logger.info("application_stopped", service=settings.app_name)


def create_app() -> FastAPI:
    """Create the HTTP application without initializing domain services."""
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )
    application.state.password_work_limiter = PasswordWorkLimiter(settings.argon2_max_concurrency)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-CSRF-Token",
            "X-Request-ID",
            "Idempotency-Key",
        ],
        expose_headers=["X-Request-ID", "X-API-Version"],
        max_age=600,
    )
    application.middleware("http")(private_response_cache_control_middleware)
    application.middleware("http")(request_context_middleware)
    register_exception_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()
