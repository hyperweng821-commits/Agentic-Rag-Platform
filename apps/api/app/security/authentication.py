"""Opaque server-side session authentication and CSRF validation."""

import hashlib
import hmac
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.errors import AppException
from app.db.models import UserSession
from app.db.repositories import UserRepository, UserSessionRepository
from app.security.passwords import (
    Argon2idPasswordHasher,
    PasswordHasher,
    PasswordWorkLimiter,
    validate_password_length,
)
from app.security.principal import Principal, normalize_email

_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,512}$")

Clock = Callable[[], datetime]
TokenFactory = Callable[[], str]


class AuthenticationError(AppException):
    """Generic failure for all missing, malformed, or unusable sessions."""

    code = "AUTHENTICATION_REQUIRED"
    message = "Authentication is required."
    status_code = status.HTTP_401_UNAUTHORIZED


class CsrfError(AppException):
    """Generic failure for missing or invalid CSRF proof."""

    code = "CSRF_VALIDATION_FAILED"
    message = "CSRF validation failed."
    status_code = status.HTTP_403_FORBIDDEN


@dataclass(frozen=True, slots=True)
class SessionCredentials:
    """One newly issued session, including raw values returned only to its caller."""

    principal: Principal
    session_token: str
    csrf_token: str
    expires_at: datetime


def utc_now() -> datetime:
    """Return an aware UTC timestamp; injectable for deterministic tests."""
    return datetime.now(UTC)


def generate_opaque_token() -> str:
    """Generate a URL-safe token backed by 256 bits of system randomness."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return the lowercase SHA-256 digest persisted for an opaque token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthenticationService:
    """Authenticate local users and own opaque server-side session lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        session_ttl: timedelta,
        password_work_limiter: PasswordWorkLimiter,
        password_hasher: PasswordHasher | None = None,
        clock: Clock = utc_now,
        token_factory: TokenFactory = generate_opaque_token,
    ) -> None:
        if session_ttl <= timedelta(0):
            raise ValueError("Session TTL must be positive.")
        self._session = session
        self._session_ttl = session_ttl
        self._password_hasher = (
            password_hasher if password_hasher is not None else _default_password_hasher()
        )
        self._password_work_limiter = password_work_limiter
        self._clock = clock
        self._token_factory = token_factory
        self._users = UserRepository(session)
        self._sessions = UserSessionRepository(session)

    async def login(self, *, email: str, password: str) -> SessionCredentials:
        """Verify local credentials and persist only digests for a new session."""
        try:
            normalized_email = normalize_email(email)
            validate_password_length(password)
        except ValueError as exc:
            raise AuthenticationError from exc

        now = self._now()
        async with self._session.begin():
            observed = await self._users.get_for_authentication_by_email(normalized_email)

        observed_password_hash = None if observed is None else observed.password_hash
        password_valid = await self._password_work_limiter.run(
            self._password_hasher.verify_password,
            password,
            observed_password_hash,
        )
        if observed is None or not password_valid or not observed.is_active:
            raise AuthenticationError

        replacement_hash: str | None = None
        if self._password_hasher.needs_rehash(observed.password_hash):
            replacement_hash = await self._password_work_limiter.run(
                self._password_hasher.hash_password,
                password,
            )

        session_token, csrf_token = self._new_token_pair()
        expires_at = now + self._session_ttl
        async with self._session.begin():
            user = await self._users.get_locked_for_authentication(observed.user_id)
            if (
                user is None
                or not user.is_active
                or not hmac.compare_digest(user.password_hash, observed.password_hash)
            ):
                raise AuthenticationError
            if replacement_hash is not None:
                await self._users.update_password_hash_for_authentication(
                    user,
                    password_hash=replacement_hash,
                )
            user_session = UserSession(
                user_id=user.id,
                token_sha256=hash_token(session_token),
                csrf_token_sha256=hash_token(csrf_token),
                expires_at=expires_at,
            )
            await self._sessions.add_for_authentication(user_session)

        return SessionCredentials(
            principal=Principal(
                user_id=user.id,
                email=user.email,
                session_id=user_session.id,
            ),
            session_token=session_token,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )

    async def authenticate_session(self, session_token: str | None) -> Principal:
        """Resolve an active session to a model-independent principal."""
        token_digest = self._session_digest_or_error(session_token)
        now = self._now()
        async with self._session.begin():
            user_session = await self._active_session(token_digest, now)
            await self._sessions.touch_for_authentication(user_session, seen_at=now)
            return self._principal(user_session)

    async def validate_csrf(
        self,
        *,
        session_token: str | None,
        csrf_token: str | None,
    ) -> None:
        """Validate a request token against the digest bound to its session."""
        token_digest = self._session_digest_or_error(session_token)
        if csrf_token is None or _TOKEN_PATTERN.fullmatch(csrf_token) is None:
            raise CsrfError
        csrf_digest = hash_token(csrf_token)
        now = self._now()
        async with self._session.begin():
            user_session = await self._active_session(token_digest, now)
            if not hmac.compare_digest(user_session.csrf_token_sha256, csrf_digest):
                raise CsrfError

    async def revoke_session(self, session_token: str | None) -> None:
        """Revoke the current server-side session without persisting its raw token."""
        token_digest = self._session_digest_or_error(session_token)
        now = self._now()
        async with self._session.begin():
            user_session = await self._active_session(token_digest, now)
            await self._sessions.revoke_for_authentication(user_session, revoked_at=now)

    async def _active_session(self, token_digest: str, now: datetime) -> UserSession:
        user_session = await self._sessions.get_active_for_authentication_by_token_sha256(
            token_digest,
            now=now,
        )
        if user_session is None:
            raise AuthenticationError
        if not hmac.compare_digest(user_session.token_sha256, token_digest):
            raise AuthenticationError
        if (
            user_session.revoked_at is not None
            or not _is_aware(user_session.expires_at)
            or user_session.expires_at <= now
            or not user_session.user.is_active
        ):
            raise AuthenticationError
        return user_session

    def _new_token_pair(self) -> tuple[str, str]:
        session_token = self._token_factory()
        csrf_token = self._token_factory()
        if (
            _TOKEN_PATTERN.fullmatch(session_token) is None
            or _TOKEN_PATTERN.fullmatch(csrf_token) is None
            or hmac.compare_digest(session_token, csrf_token)
        ):
            raise RuntimeError("Token factory returned invalid authentication material.")
        return session_token, csrf_token

    def _now(self) -> datetime:
        now = self._clock()
        if not _is_aware(now):
            raise RuntimeError("Authentication clock must return a timezone-aware timestamp.")
        return now

    @staticmethod
    def _session_digest_or_error(session_token: str | None) -> str:
        if session_token is None or _TOKEN_PATTERN.fullmatch(session_token) is None:
            raise AuthenticationError
        return hash_token(session_token)

    @staticmethod
    def _principal(user_session: UserSession) -> Principal:
        return Principal(
            user_id=user_session.user.id,
            email=user_session.user.email,
            session_id=user_session.id,
        )


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


@lru_cache(maxsize=1)
def _default_password_hasher() -> Argon2idPasswordHasher:
    """Reuse one thread-safe hasher and unknown-user digest across requests."""
    return Argon2idPasswordHasher()
