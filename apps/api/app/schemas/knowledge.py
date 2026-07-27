"""Strict AF-1 knowledge-intake API contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import APIModel


class KnowledgeBaseCreate(APIModel):
    """Input for creating one knowledge base."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Reject whitespace-only names and persist a canonical trimmed name."""
        value = value.strip()
        if not value:
            raise ValueError("Knowledge-base name must not be blank")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Normalize blank optional descriptions to null."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class KnowledgeBaseResponse(APIModel):
    """Public knowledge-base metadata."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseListResponse(APIModel):
    """Bounded deterministic knowledge-base page."""

    items: list[KnowledgeBaseResponse]
    limit: int
    offset: int


class DocumentResponse(APIModel):
    """Public document metadata without an absolute storage path."""

    id: UUID
    knowledge_base_id: UUID
    original_filename: str
    media_type: str
    size_bytes: int
    sha256: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(APIModel):
    """Bounded deterministic document page."""

    items: list[DocumentResponse]
    limit: int
    offset: int


class IngestionJobResponse(APIModel):
    """Public durable ingestion-job state."""

    id: UUID
    document_id: UUID
    status: Literal["pending", "processing", "completed", "failed"]
    attempt_count: int
    error_code: str | None
    safe_error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime


class DocumentUploadResponse(APIModel):
    """New or deduplicated document upload result."""

    document: DocumentResponse
    ingestion_job: IngestionJobResponse
    duplicate: bool
