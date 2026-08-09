"""Safe product projection for final-authoritative Hybrid Retrieval records."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.retrieval.hybrid import HybridRetrievalResult
from app.retrieval.service import UNTRUSTED_DOCUMENT_CONTENT, RetrievalUnavailableError


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    """One public evidence item with trusted provenance and classified content."""

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


def project_retrieved_evidence(
    result: HybridRetrievalResult,
) -> tuple[RetrievedEvidence, ...]:
    """Project only final PostgreSQL-authoritative records into product evidence."""
    projected: list[RetrievedEvidence] = []
    for record in result.records:
        authoritative = record.authoritative
        trusted = authoritative.trusted
        document_content = authoritative.document_content
        if document_content.trust_classification != UNTRUSTED_DOCUMENT_CONTENT:
            raise RetrievalUnavailableError
        projected.append(
            RetrievedEvidence(
                citation_id=trusted.chunk_id,
                document_id=trusted.document_id,
                source_display_name=trusted.source_display_name,
                content=document_content.text,
                content_sha256=trusted.content_sha256,
                page_start=trusted.page_start,
                page_end=trusted.page_end,
                character_start=trusted.character_start,
                character_end=trusted.character_end,
                trust_classification="untrusted_document_content",
                fused_rank=record.fused_rank,
                keyword_rank=record.keyword_rank,
                dense_rank=record.dense_rank,
            )
        )
    return tuple(projected)
