"""Stable application exceptions and global HTTP error handlers."""

from typing import Any, ClassVar, cast

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from app.api.cache_control import private_cache_headers
from app.core.logging import API_VERSION, API_VERSION_HEADER, REQUEST_ID_HEADER, get_request_id
from app.schemas.common import ErrorInfo, ErrorResponse, ValidationIssue

logger = structlog.get_logger(__name__)


class AppException(Exception):
    """Base exception for safe, intentional application failures."""

    code: ClassVar[str] = "APPLICATION_ERROR"
    message: ClassVar[str] = "The request could not be completed."
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(message or self.message)
        self.public_message = message or self.message
        self.details = details


class BadRequestError(AppException):
    """The caller supplied a semantically invalid request."""

    code = "BAD_REQUEST"
    message = "The request is invalid."
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundError(AppException):
    """The requested resource does not exist."""

    code = "NOT_FOUND"
    message = "The requested resource was not found."
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppException):
    """The request conflicts with current server state."""

    code = "CONFLICT"
    message = "The request conflicts with the current resource state."
    status_code = status.HTTP_409_CONFLICT


class InvalidUploadError(BadRequestError):
    """The uploaded file failed AF-1 filename or content validation."""

    code = "INVALID_UPLOAD"
    message = "The uploaded file is invalid."


class UnsupportedMediaTypeError(AppException):
    """The uploaded filename and declared media type are not supported."""

    code = "UNSUPPORTED_MEDIA_TYPE"
    message = "The uploaded file type is not supported."
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


class UploadTooLargeError(AppException):
    """The upload exceeded the configured streaming size limit."""

    code = "UPLOAD_TOO_LARGE"
    message = "The uploaded file exceeds the maximum allowed size."
    status_code = status.HTTP_413_CONTENT_TOO_LARGE


class ServiceUnavailableError(AppException):
    """A required infrastructure dependency is temporarily unavailable."""

    code = "SERVICE_UNAVAILABLE"
    message = "A required service is temporarily unavailable."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class DatabaseUnavailableError(ServiceUnavailableError):
    """PostgreSQL did not pass the readiness check."""

    code = "DATABASE_UNAVAILABLE"
    message = "Database is unavailable."

    def __init__(self) -> None:
        super().__init__(details={"database": "unhealthy"})


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)
    payload = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details,
            request_id=request_id,
        )
    )
    headers = {
        REQUEST_ID_HEADER: request_id,
        API_VERSION_HEADER: API_VERSION,
    }
    headers.update(private_cache_headers(request.url.path))
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Serialize an intentional application exception."""
    logger.warning(
        "application_error",
        code=exc.code,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.public_message,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a stable, JSON-safe representation of validation failures."""
    issues = [
        ValidationIssue(
            location=[str(part) if not isinstance(part, int) else part for part in error["loc"]],
            message=error["msg"],
            error_type=error["type"],
        ).model_dump(mode="json")
        for error in exc.errors()
    ]
    return _error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=issues,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Normalize framework-generated errors, including 404 responses."""
    is_not_found = exc.status_code == status.HTTP_404_NOT_FOUND
    message = "The requested resource was not found." if is_not_found else str(exc.detail)
    code = "NOT_FOUND" if is_not_found else f"HTTP_{exc.status_code}"
    return _error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Hide internal details while logging an unknown server failure."""
    request_id = get_request_id(request)
    logger.exception(
        "unhandled_exception",
        error_type=type(exc).__name__,
        path=request.url.path,
        request_id=request_id,
    )
    return _error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal error occurred.",
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Register every public exception boundary on an application instance."""
    application.add_exception_handler(
        AppException,
        cast(ExceptionHandler, app_exception_handler),
    )
    application.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_exception_handler),
    )
    application.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, http_exception_handler),
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)
