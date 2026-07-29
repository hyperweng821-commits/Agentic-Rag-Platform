"""Narrow Argon2id password-hashing boundary."""

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import ParamSpec, Protocol, TypeVar

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

MIN_PASSWORD_LENGTH = 1
MAX_PASSWORD_LENGTH = 1024

_P = ParamSpec("_P")
_R = TypeVar("_R")


class PasswordHasher(Protocol):
    """Password operations consumed by authentication and operator setup."""

    def hash_password(self, password: str) -> str:
        """Return a one-way password hash suitable for persistence."""
        ...

    def verify_password(self, password: str, password_hash: str | None) -> bool:
        """Verify a password, including a timing-safe path for unknown users."""
        ...

    def needs_rehash(self, password_hash: str) -> bool:
        """Return whether a verified hash should be replaced."""
        ...


class PasswordWorkLimiter:
    """Run memory-intensive password work on one bounded application executor."""

    def __init__(self, max_concurrency: int) -> None:
        if not 1 <= max_concurrency <= 8:
            raise ValueError("Password work concurrency must be between 1 and 8.")
        self.max_concurrency = max_concurrency
        self._executor = ThreadPoolExecutor(
            max_workers=max_concurrency,
            thread_name_prefix="agentforge-argon2",
        )

    async def run(
        self,
        operation: Callable[_P, _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _R:
        """Run one operation without blocking the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(operation, *args, **kwargs),
        )

    def shutdown(self) -> None:
        """Release executor threads after application shutdown."""
        self._executor.shutdown(wait=True, cancel_futures=False)


def validate_password_length(password: str) -> None:
    """Enforce the shared password bounds without reproducing the input."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must not be empty.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must not exceed {MAX_PASSWORD_LENGTH} characters.")


class Argon2idPasswordHasher:
    """Hash and verify passwords using argon2-cffi's Argon2id profile."""

    def __init__(self, hasher: Argon2PasswordHasher | None = None) -> None:
        self._hasher = hasher or Argon2PasswordHasher(type=Type.ID)
        self._unknown_user_hash: str | None = None

    def hash_password(self, password: str) -> str:
        """Hash a non-empty password with a fresh Argon2id salt."""
        validate_password_length(password)
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str | None) -> bool:
        """Return false for mismatches, malformed hashes, and unknown users."""
        try:
            validate_password_length(password)
        except ValueError:
            return False
        dummy_hash = self._dummy_hash()
        known_user = password_hash is not None
        candidate_hash = dummy_hash if password_hash is None else password_hash

        try:
            verified = self._hasher.verify(candidate_hash, password)
        except (InvalidHashError, VerificationError):
            return False
        return known_user and verified

    def needs_rehash(self, password_hash: str) -> bool:
        """Return false for malformed hashes and true for outdated parameters."""
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except InvalidHashError:
            return False

    def _dummy_hash(self) -> str:
        """Lazily create one salted process-local unknown-user hash."""
        if self._unknown_user_hash is None:
            self._unknown_user_hash = self._hasher.hash(
                "agentforge-unknown-user-timing-equalization"
            )
        return self._unknown_user_hash
