"""Stable authenticated-principal value object."""

from dataclasses import dataclass
from uuid import UUID

MAX_EMAIL_LENGTH = 320


def normalize_email(email: str) -> str:
    """Normalize the bounded local-user identifier used for lookup and storage."""
    normalized = email.strip().lower()
    if not normalized:
        raise ValueError("Email must not be blank.")
    if len(normalized) > MAX_EMAIL_LENGTH:
        raise ValueError(f"Email must not exceed {MAX_EMAIL_LENGTH} characters.")
    return normalized


@dataclass(frozen=True, slots=True)
class Principal:
    """Authentication result exposed to HTTP and application-service layers."""

    user_id: UUID
    email: str
    session_id: UUID
