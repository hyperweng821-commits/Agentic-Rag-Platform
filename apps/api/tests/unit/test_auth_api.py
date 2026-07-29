"""AF-2S1 local authentication HTTP boundary tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from app.api.dependencies import get_authentication_service, get_csrf_protected_principal
from app.core.config import get_settings
from app.security import (
    MAX_PASSWORD_LENGTH,
    AuthenticationError,
    AuthenticationService,
    CsrfError,
    Principal,
    SessionCredentials,
)

SESSION_TOKEN = "s" * 43
CSRF_TOKEN = "c" * 43


@pytest.fixture
def authentication(application: FastAPI) -> AsyncMock:
    """Replace session persistence while retaining the real HTTP dependencies."""
    service = AsyncMock(spec=AuthenticationService)
    application.dependency_overrides[get_authentication_service] = lambda: service
    return service


def _principal() -> Principal:
    return Principal(
        user_id=uuid4(),
        email="owner@example.com",
        session_id=uuid4(),
    )


def _credentials(principal: Principal) -> SessionCredentials:
    return SessionCredentials(
        principal=principal,
        session_token=SESSION_TOKEN,
        csrf_token=CSRF_TOKEN,
        expires_at=datetime.now(UTC) + timedelta(hours=8),
    )


def _cookie_header(response_headers: list[str], cookie_name: str) -> str:
    prefix = f"{cookie_name}="
    return next(header for header in response_headers if header.startswith(prefix))


async def test_login_sets_exact_session_and_csrf_cookie_boundaries(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    principal = _principal()
    authentication.login.return_value = _credentials(principal)
    password = "".join(("local-", "passphrase"))

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": " Owner@Example.COM ", "password": password},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(principal.user_id),
        "email": principal.email,
    }
    assert response.headers["cache-control"] == "private, no-store"
    authentication.login.assert_awaited_once_with(
        email="Owner@Example.COM",
        password=password,
    )

    cookie_headers = response.headers.get_list("set-cookie")
    session_cookie = _cookie_header(cookie_headers, "agentforge_session")
    csrf_cookie = _cookie_header(cookie_headers, "agentforge_csrf")

    assert session_cookie.startswith(f"agentforge_session={SESSION_TOKEN};")
    assert "HttpOnly" in session_cookie
    assert "Max-Age=28800" in session_cookie
    assert "; Path=/api/v1;" in session_cookie
    assert "SameSite=strict" in session_cookie
    assert "Secure" not in session_cookie

    assert csrf_cookie.startswith(f"agentforge_csrf={CSRF_TOKEN};")
    assert "HttpOnly" not in csrf_cookie
    assert "Max-Age=28800" in csrf_cookie
    assert "; Path=/;" in csrf_cookie
    assert "SameSite=strict" in csrf_cookie
    assert "Secure" not in csrf_cookie


async def test_login_failure_uses_generic_authentication_error(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    password = "".join(("incorrect-", "passphrase"))
    authentication.login.side_effect = AuthenticationError

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": password},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["message"] == "Authentication is required."
    assert "unknown@example.com" not in response.text
    assert password not in response.text
    assert response.headers.get_list("set-cookie") == []
    assert response.headers["cache-control"] == "private, no-store"


async def test_login_marks_both_cookies_secure_when_configured(
    client: AsyncClient,
    authentication: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    authentication.login.return_value = _credentials(_principal())

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@example.com",
            "password": "".join(("local-", "passphrase")),
        },
    )

    assert response.status_code == 200
    cookie_headers = response.headers.get_list("set-cookie")
    assert "Secure" in _cookie_header(cookie_headers, "agentforge_session")
    assert "Secure" in _cookie_header(cookie_headers, "agentforge_csrf")


async def test_me_resolves_the_opaque_session_without_exposing_authentication_material(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    principal = _principal()
    authentication.authenticate_session.return_value = principal
    client.cookies.set("agentforge_session", SESSION_TOKEN, path="/api/v1")

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(principal.user_id),
        "email": principal.email,
    }
    assert "session_id" not in response.json()
    assert response.headers["cache-control"] == "private, no-store"
    assert SESSION_TOKEN not in response.text
    assert CSRF_TOKEN not in response.text
    authentication.authenticate_session.assert_awaited_once_with(SESSION_TOKEN)


async def test_missing_or_invalid_session_returns_one_generic_unauthorized_response(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    authentication.authenticate_session.side_effect = AuthenticationError

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["message"] == "Authentication is required."
    assert response.headers["cache-control"] == "private, no-store"
    authentication.authenticate_session.assert_awaited_once_with(None)


async def test_logout_validates_csrf_revokes_session_and_clears_both_cookies(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    principal = _principal()
    authentication.authenticate_session.return_value = principal
    client.cookies.set("agentforge_session", SESSION_TOKEN, path="/api/v1")
    client.cookies.set("agentforge_csrf", CSRF_TOKEN, path="/")

    response = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": CSRF_TOKEN},
    )

    assert response.status_code == 204
    assert response.headers["cache-control"] == "private, no-store"
    authentication.authenticate_session.assert_awaited_once_with(SESSION_TOKEN)
    authentication.validate_csrf.assert_awaited_once_with(
        session_token=SESSION_TOKEN,
        csrf_token=CSRF_TOKEN,
    )
    authentication.revoke_session.assert_awaited_once_with(SESSION_TOKEN)

    cookie_headers = response.headers.get_list("set-cookie")
    session_cookie = _cookie_header(cookie_headers, "agentforge_session")
    csrf_cookie = _cookie_header(cookie_headers, "agentforge_csrf")
    assert "Max-Age=0" in session_cookie
    assert "; Path=/api/v1;" in session_cookie
    assert "SameSite=strict" in session_cookie
    assert "HttpOnly" in session_cookie
    assert "Max-Age=0" in csrf_cookie
    assert "; Path=/;" in csrf_cookie
    assert "SameSite=strict" in csrf_cookie
    assert "HttpOnly" not in csrf_cookie


@pytest.mark.parametrize(
    ("csrf_cookie", "csrf_header"),
    [
        (None, None),
        (CSRF_TOKEN, None),
        (None, CSRF_TOKEN),
        (CSRF_TOKEN, "d" * 43),
    ],
    ids=["both-missing", "header-missing", "cookie-missing", "mismatch"],
)
async def test_logout_rejects_missing_or_mismatched_double_submit_csrf(
    client: AsyncClient,
    authentication: AsyncMock,
    csrf_cookie: str | None,
    csrf_header: str | None,
) -> None:
    authentication.authenticate_session.return_value = _principal()
    client.cookies.set("agentforge_session", SESSION_TOKEN, path="/api/v1")
    if csrf_cookie is not None:
        client.cookies.set("agentforge_csrf", csrf_cookie, path="/")
    headers = {} if csrf_header is None else {"X-CSRF-Token": csrf_header}

    response = await client.post("/api/v1/auth/logout", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    assert response.headers["cache-control"] == "private, no-store"
    authentication.validate_csrf.assert_not_awaited()
    authentication.revoke_session.assert_not_awaited()


async def test_logout_rejects_csrf_not_bound_to_the_server_session(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    authentication.authenticate_session.return_value = _principal()
    authentication.validate_csrf.side_effect = CsrfError
    client.cookies.set("agentforge_session", SESSION_TOKEN, path="/api/v1")
    client.cookies.set("agentforge_csrf", CSRF_TOKEN, path="/")

    response = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": CSRF_TOKEN},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    authentication.revoke_session.assert_not_awaited()


@pytest.mark.parametrize(
    ("cookie_value", "header_value", "reaches_digest_validation"),
    [
        (b"\xff", b"\xff", True),
        (b"\xff", b"\xfe", False),
    ],
)
async def test_non_ascii_csrf_proof_fails_closed_without_type_error(
    authentication: AsyncMock,
    cookie_value: bytes,
    header_value: bytes,
    reaches_digest_validation: bool,
) -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/logout",
            "headers": [
                (
                    b"cookie",
                    b"agentforge_session="
                    + SESSION_TOKEN.encode()
                    + b"; agentforge_csrf="
                    + cookie_value,
                ),
                (b"x-csrf-token", header_value),
            ],
        }
    )
    authentication.validate_csrf.side_effect = CsrfError

    with pytest.raises(CsrfError):
        await get_csrf_protected_principal(
            request,
            _principal(),
            authentication,
            get_settings(),
        )

    if reaches_digest_validation:
        authentication.validate_csrf.assert_awaited_once()
    else:
        authentication.validate_csrf.assert_not_awaited()


async def test_over_limit_http_password_is_rejected_without_authentication_or_disclosure(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    password = "p" * (MAX_PASSWORD_LENGTH + 1)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": password},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert password not in response.text
    assert response.headers["cache-control"] == "private, no-store"
    authentication.login.assert_not_awaited()


async def test_http_login_accepts_the_shared_maximum_password_length(
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    principal = _principal()
    authentication.login.return_value = _credentials(principal)
    password = "p" * MAX_PASSWORD_LENGTH

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": password},
    )

    assert response.status_code == 200
    authentication.login.assert_awaited_once_with(
        email="owner@example.com",
        password=password,
    )


def test_public_auth_schema_excludes_internal_session_identifier(
    application: FastAPI,
) -> None:
    schema = application.openapi()["components"]["schemas"]["AuthenticatedUserResponse"]

    assert set(schema["properties"]) == {"id", "email"}
