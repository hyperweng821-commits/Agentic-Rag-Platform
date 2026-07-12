"""Service and PostgreSQL readiness endpoint."""

import asyncio

import structlog
from fastapi import APIRouter, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import AppSettings, DatabaseSession
from app.api.errors import DatabaseUnavailableError
from app.db.session import check_database_connection
from app.schemas.common import ErrorResponse, HealthResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check service readiness",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "PostgreSQL is unavailable",
        }
    },
)
async def health_check(
    session: DatabaseSession,
    settings: AppSettings,
) -> HealthResponse:
    """Report readiness only after PostgreSQL responds to a minimal query."""
    try:
        async with asyncio.timeout(settings.database_healthcheck_timeout_seconds):
            await check_database_connection(session)
    except (TimeoutError, SQLAlchemyError) as exc:
        logger.warning("database_health_check_failed", error_type=type(exc).__name__)
        raise DatabaseUnavailableError() from exc

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        database="healthy",
    )
