"""Tests for the public error protocol and global exception handlers."""

from typing import Annotated

from fastapi import FastAPI, Query
from httpx import AsyncClient

from app.api.errors import NotFoundError


async def test_unknown_route_returns_unified_404(client: AsyncClient) -> None:
    response = await client.get("/route-that-does-not-exist")
    payload = response.json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["message"] == "The requested resource was not found."
    assert payload["error"]["details"] is None
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["X-API-Version"] == "1"


async def test_request_validation_error_uses_unified_format(
    application: FastAPI,
    client: AsyncClient,
) -> None:
    @application.get("/_test/validation", include_in_schema=False)
    async def validation_endpoint(
        page_size: Annotated[int, Query(ge=1, le=100)],
    ) -> dict[str, int]:
        return {"page_size": page_size}

    response = await client.get("/_test/validation", params={"page_size": 0})
    payload = response.json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["message"] == "Request validation failed."
    assert payload["error"]["details"] == [
        {
            "location": ["query", "page_size"],
            "message": "Input should be greater than or equal to 1",
            "error_type": "greater_than_equal",
        }
    ]
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]


async def test_custom_exception_handler_returns_public_error(
    application: FastAPI,
    client: AsyncClient,
) -> None:
    @application.get("/_test/custom-error", include_in_schema=False)
    async def custom_error_endpoint() -> None:
        raise NotFoundError("Synthetic resource was not found.", details={"resource": "test"})

    response = await client.get("/_test/custom-error")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Synthetic resource was not found.",
        "details": {"resource": "test"},
        "request_id": response.headers["X-Request-ID"],
    }


async def test_unknown_exception_is_hidden_by_fallback_handler(
    application: FastAPI,
    client: AsyncClient,
) -> None:
    @application.get("/_test/unknown-error", include_in_schema=False)
    async def unknown_error_endpoint() -> None:
        raise RuntimeError("private implementation detail")

    response = await client.get("/_test/unknown-error")

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected internal error occurred.",
        "details": None,
        "request_id": response.headers["X-Request-ID"],
    }
    assert "private implementation detail" not in response.text
