"""Central cache policy for cookie-authenticated API responses."""

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

PRIVATE_CACHE_CONTROL = "private, no-store"
_API_PREFIX = "/api/v1"
_PUBLIC_HEALTH_PATH = f"{_API_PREFIX}/health"


def is_private_api_path(path: str) -> bool:
    """Default API responses to private except the explicit public health route."""
    normalized = path.rstrip("/") or "/"
    return normalized.startswith(f"{_API_PREFIX}/") and normalized != _PUBLIC_HEALTH_PATH


def private_cache_headers(path: str) -> dict[str, str]:
    """Return the cache header required for one request path."""
    if not is_private_api_path(path):
        return {}
    return {"Cache-Control": PRIVATE_CACHE_CONTROL}


async def private_response_cache_control_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Prevent shared or browser caching of private API responses."""
    response = await call_next(request)
    if is_private_api_path(request.url.path):
        response.headers["Cache-Control"] = PRIVATE_CACHE_CONTROL
    return response
