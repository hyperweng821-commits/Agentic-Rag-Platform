"""Strict public request and response schemas for product retrieval."""

from typing import Literal
from uuid import UUID

from pydantic import Field, StrictInt, StrictStr

from app.schemas.common import APIModel


class RetrievalQueryRequest(APIModel):
    """Structurally valid input passed to the canonical retrieval parser."""

    query: StrictStr
    requested_count: StrictInt = Field(default=10, ge=1, le=50)


class RetrievalEvidenceResponse(APIModel):
    """One final-authoritative product evidence item."""

    citation_id: UUID
    document_id: UUID
    source_display_name: str
    content: str
    content_sha256: str
    page_start: int | None
    page_end: int | None
    character_start: int | None
    character_end: int | None
    trust_classification: Literal["untrusted_document_content"]
    fused_rank: int
    keyword_rank: int | None
    dense_rank: int | None


class RetrievalResponse(APIModel):
    """Public evidence envelope without query or diagnostic metadata."""

    items: list[RetrievalEvidenceResponse]
