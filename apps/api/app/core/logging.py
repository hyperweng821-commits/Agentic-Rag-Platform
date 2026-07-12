"""Structured logging and request-correlation infrastructure."""

import logging
import re
import sys
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request, Response

from app.core.config import Settings

REQUEST_ID_HEADER = "X-Request-ID"
API_VERSION_HEADER = "X-API-Version"
API_VERSION = "1"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def configure_logging(settings: Settings) -> None:
    """Configure stdlib and structlog through one safe output pipeline."""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]
    renderer: structlog.types.Processor
    if settings.use_json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )

    structlog_processors: list[structlog.types.Processor] = [
        *shared_processors,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    if settings.use_json_logs:
        structlog_processors.append(structlog.processors.format_exc_info)
    structlog_processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)

    structlog.configure(
        processors=structlog_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_request_id(request: Request) -> str:
    """Return the validated request ID stored by the request middleware."""
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and _REQUEST_ID_PATTERN.fullmatch(request_id):
        return request_id
    request_id = str(uuid4())
    request.state.request_id = request_id
    return request_id


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Bind request context, emit access logs, and return correlation headers."""
    incoming_request_id = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = (
        incoming_request_id if _REQUEST_ID_PATTERN.fullmatch(incoming_request_id) else str(uuid4())
    )
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    logger = structlog.get_logger("app.request")
    started_at = perf_counter()
    logger.info("request_started", method=request.method, path=request.url.path)
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
        )
        raise
    else:
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[API_VERSION_HEADER] = API_VERSION
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
        )
        return response
    finally:
        structlog.contextvars.clear_contextvars()
