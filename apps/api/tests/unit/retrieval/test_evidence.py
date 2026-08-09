"""Product evidence projection tests for final-authoritative retrieval records."""

import hashlib
from dataclasses import fields
from uuid import UUID, uuid4

from app.retrieval.evidence import RetrievedEvidence, project_retrieved_evidence
from app.retrieval.hybrid import (
    HybridRetrievalResult,
    _FusedInternalAuthoritativeRetrievalRecord,
)
from app.retrieval.service import (
    _InternalAuthoritativeRetrievalRecord,
    _TrustedAuthoritativeProvenance,
    _UntrustedDocumentContent,
)


def _record(
    *,
    chunk_id: UUID,
    content: str,
    fused_rank: int,
    keyword_rank: int | None,
    dense_rank: int | None,
) -> _FusedInternalAuthoritativeRetrievalRecord:
    return _FusedInternalAuthoritativeRetrievalRecord(
        authoritative=_InternalAuthoritativeRetrievalRecord(
            trusted=_TrustedAuthoritativeProvenance(
                knowledge_base_id=uuid4(),
                document_id=uuid4(),
                chunk_id=chunk_id,
                content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                source_display_name=f"source-{fused_rank}.md",
                page_start=fused_rank,
                page_end=fused_rank + 1,
                character_start=10 * fused_rank,
                character_end=10 * fused_rank + len(content),
            ),
            document_content=_UntrustedDocumentContent(text=content),
        ),
        keyword_rank=keyword_rank,
        dense_rank=dense_rank,
        fused_numerator=123,
        fused_denominator=456,
        fused_rank=fused_rank,
    )


def test_projection_uses_only_authoritative_content_provenance_and_final_ranks() -> None:
    first = _record(
        chunk_id=uuid4(),
        content="authoritative first content",
        fused_rank=1,
        keyword_rank=2,
        dense_rank=1,
    )
    second = _record(
        chunk_id=uuid4(),
        content="authoritative second content",
        fused_rank=2,
        keyword_rank=None,
        dense_rank=3,
    )

    projected = project_retrieved_evidence(HybridRetrievalResult(records=(first, second)))

    assert isinstance(projected, tuple)
    assert [item.citation_id for item in projected] == [
        first.authoritative.trusted.chunk_id,
        second.authoritative.trusted.chunk_id,
    ]
    assert [item.content for item in projected] == [
        first.authoritative.document_content.text,
        second.authoritative.document_content.text,
    ]
    for source, item in zip((first, second), projected, strict=True):
        trusted = source.authoritative.trusted
        assert item.citation_id == trusted.chunk_id
        assert item.document_id == trusted.document_id
        assert item.source_display_name == trusted.source_display_name
        assert item.content_sha256 == trusted.content_sha256
        assert item.page_start == trusted.page_start
        assert item.page_end == trusted.page_end
        assert item.character_start == trusted.character_start
        assert item.character_end == trusted.character_end
        assert item.trust_classification == "untrusted_document_content"
        assert item.fused_rank == source.fused_rank
        assert item.keyword_rank == source.keyword_rank
        assert item.dense_rank == source.dense_rank


def test_product_projection_has_exact_safe_field_manifest() -> None:
    assert RetrievedEvidence.__slots__ == (
        "citation_id",
        "document_id",
        "source_display_name",
        "content",
        "content_sha256",
        "page_start",
        "page_end",
        "character_start",
        "character_end",
        "trust_classification",
        "fused_rank",
        "keyword_rank",
        "dense_rank",
    )
    assert {field.name for field in fields(RetrievedEvidence)} == set(RetrievedEvidence.__slots__)
    for forbidden in (
        "knowledge_base_id",
        "provider_response",
        "chroma_distance",
        "fused_numerator",
        "fused_denominator",
        "rejected_candidate",
        "proof",
        "session_token_sha256",
    ):
        assert forbidden not in RetrievedEvidence.__slots__
