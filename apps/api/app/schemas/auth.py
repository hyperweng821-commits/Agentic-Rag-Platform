"""Public contracts for the bounded local-session authentication API."""

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import APIModel
from app.security.passwords import MAX_PASSWORD_LENGTH


class LoginRequest(APIModel):
    """Credentials accepted only by the local login endpoint."""

    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def trim_email(cls, value: str) -> str:
        """Reject an email containing only whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("Email must not be blank")
        return value


class AuthenticatedUserResponse(APIModel):
    """The non-sensitive principal fields safe to expose to a client."""

    id: UUID
    email: str
