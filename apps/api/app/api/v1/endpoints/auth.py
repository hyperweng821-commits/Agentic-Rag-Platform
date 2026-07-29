"""Bounded local authentication endpoints backed by opaque server sessions."""

from fastapi import APIRouter, Request, Response, status

from app.api.dependencies import (
    AppSettings,
    Authentication,
    CsrfProtectedPrincipal,
    CurrentPrincipal,
)
from app.schemas.auth import AuthenticatedUserResponse, LoginRequest
from app.security import Principal

_SESSION_COOKIE_PATH = "/api/v1"
_CSRF_COOKIE_PATH = "/"

router = APIRouter()


@router.post(
    "/login",
    response_model=AuthenticatedUserResponse,
    summary="Start a local authenticated session",
)
async def login(
    payload: LoginRequest,
    response: Response,
    authentication: Authentication,
    settings: AppSettings,
) -> AuthenticatedUserResponse:
    """Verify local credentials and issue opaque session and CSRF cookies."""
    credentials = await authentication.login(
        email=payload.email,
        password=payload.password,
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=credentials.session_token,
        max_age=settings.session_ttl_seconds,
        path=_SESSION_COOKIE_PATH,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=credentials.csrf_token,
        max_age=settings.session_ttl_seconds,
        path=_CSRF_COOKIE_PATH,
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite=settings.session_cookie_samesite,
    )
    return _principal_response(credentials.principal)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current local session",
)
async def logout(
    request: Request,
    response: Response,
    _: CsrfProtectedPrincipal,
    authentication: Authentication,
    settings: AppSettings,
) -> None:
    """Revoke the server-side session and expire both browser cookies."""
    await authentication.revoke_session(request.cookies.get(settings.session_cookie_name))
    response.delete_cookie(
        settings.session_cookie_name,
        path=_SESSION_COOKIE_PATH,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path=_CSRF_COOKIE_PATH,
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite=settings.session_cookie_samesite,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
    summary="Retrieve the current authenticated principal",
)
async def me(principal: CurrentPrincipal) -> AuthenticatedUserResponse:
    """Return only the stable, non-sensitive principal contract."""
    return _principal_response(principal)


def _principal_response(principal: Principal) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        id=principal.user_id,
        email=principal.email,
    )
