"""Tests for application creation and the readiness contract."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from app.main import create_app


def test_application_can_be_created() -> None:
    application = create_app()

    assert isinstance(application, FastAPI)
    assert application.title == "agentic-rag-backend"
    assert "/api/v1/health" in application.openapi()["paths"]


async def test_health_check_returns_healthy(
    client: AsyncClient,
    database_session: AsyncMock,
) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "agentic-rag-backend",
        "version": "0.1.0",
        "database": "healthy",
    }
    database_session.execute.assert_awaited_once()


async def test_health_check_response_fields_are_stable(
    client: AsyncClient,
    database_session: AsyncMock,
) -> None:
    response = await client.get("/api/v1/health")
    payload = response.json()

    assert set(payload) == {"status", "service", "version", "database"}
    assert response.headers["X-API-Version"] == "1"
    assert response.headers["X-Request-ID"]
    database_session.execute.assert_awaited_once()


async def test_health_check_operational_error_returns_503(
    client: AsyncClient,
    database_session: AsyncMock,
) -> None:
    database_session.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        ConnectionError("database connection refused"),
    )

    response = await client.get("/api/v1/health")
    payload = response.json()

    assert response.status_code == 503
    assert payload["error"] == {
        "code": "DATABASE_UNAVAILABLE",
        "message": "Database is unavailable.",
        "details": {"database": "unhealthy"},
        "request_id": response.headers["X-Request-ID"],
    }
    assert "connection refused" not in response.text


async def test_health_check_returns_503_after_database_timeout(
    client: AsyncClient,
    database_session: AsyncMock,
) -> None:
    database_session.execute.side_effect = TimeoutError("database health check timed out")

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "timed out" not in response.text


@pytest.mark.parametrize(
    "internal_error",
    [
        pytest.param(RuntimeError("runtime defect"), id="runtime-error"),
        pytest.param(AttributeError("attribute defect"), id="attribute-error"),
        pytest.param(ValueError("value defect"), id="value-error"),
        pytest.param(TypeError("type defect"), id="type-error"),
    ],
)
async def test_health_check_internal_error_reaches_global_handler(
    client: AsyncClient,
    database_session: AsyncMock,
    internal_error: Exception,
) -> None:
    database_session.execute.side_effect = internal_error

    response = await client.get("/api/v1/health")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["error"]["code"] != "DATABASE_UNAVAILABLE"
    assert str(internal_error) not in response.text


async def test_cors_preflight_allows_configured_frontend(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
