"""Shared infrastructure-level API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base schema with strict, predictable serialization behavior."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class HealthResponse(APIModel):
    """Service and PostgreSQL readiness response."""

    status: Literal["healthy"]
    service: str
    version: str
    database: Literal["healthy"]


class ValidationIssue(APIModel):
    """Sanitized request-validation detail safe for public responses."""

    location: list[str | int]
    message: str
    error_type: str


class ErrorInfo(APIModel):
    """Stable public error payload."""

    code: str
    message: str
    details: Any | None = None
    request_id: str


class ErrorResponse(APIModel):
    """Envelope shared by every HTTP error response."""

    error: ErrorInfo
