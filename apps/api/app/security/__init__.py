"""Bounded local authentication and knowledge-access authorization primitives."""

from app.security.authentication import (
    AuthenticationError,
    AuthenticationService,
    CsrfError,
    SessionCredentials,
    generate_opaque_token,
    hash_token,
)
from app.security.authorization import (
    AuthorizationError,
    Capability,
    capabilities_for,
    require_capability,
)
from app.security.passwords import (
    MAX_PASSWORD_LENGTH,
    Argon2idPasswordHasher,
    PasswordHasher,
    PasswordWorkLimiter,
    validate_password_length,
)
from app.security.principal import Principal, normalize_email

__all__ = [
    "MAX_PASSWORD_LENGTH",
    "Argon2idPasswordHasher",
    "AuthenticationError",
    "AuthenticationService",
    "AuthorizationError",
    "Capability",
    "CsrfError",
    "PasswordHasher",
    "PasswordWorkLimiter",
    "Principal",
    "SessionCredentials",
    "capabilities_for",
    "generate_opaque_token",
    "hash_token",
    "normalize_email",
    "require_capability",
    "validate_password_length",
]
