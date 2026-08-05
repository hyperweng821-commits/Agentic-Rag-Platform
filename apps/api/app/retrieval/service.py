"""Provider-independent AF-3A retrieval access and keyword orchestration."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Protocol
from uuid import UUID

from app.retrieval.domain import RetrievalRequest, parse_retrieval_request
from app.security.authentication import SessionAuthenticationProof


class RetrievalAuthenticationError(Exception):
    """Signal that the preserved session proof is no longer initially usable."""

    def __init__(self) -> None:
        super().__init__("Retrieval authentication failed.")


class RetrievalTargetNotFoundError(Exception):
    """Hide an absent or inaccessible retrieval target behind one internal result."""

    def __init__(self) -> None:
        super().__init__("Retrieval target was not found.")


class RetrievalUnavailableError(Exception):
    """Hide database and adapter details from later public error mapping."""

    def __init__(self) -> None:
        super().__init__("Retrieval is unavailable.")


class FinalCandidateLimitError(ValueError):
    """Reject an unbounded final-validation input before PostgreSQL work."""


FINAL_VALIDATION_BATCH_SIZE: Final = 64
MAX_FINAL_CANDIDATES: Final = 192
UNTRUSTED_DOCUMENT_CONTENT: Final = "untrusted_document_content"


@dataclass(frozen=True, slots=True, repr=False)
class _TrustedAuthoritativeProvenance:
    """Fully loaded PostgreSQL control and provenance primitives."""

    knowledge_base_id: UUID
    document_id: UUID
    chunk_id: UUID
    content_sha256: str
    source_display_name: str
    page_start: int | None
    page_end: int | None
    character_start: int | None
    character_end: int | None


@dataclass(frozen=True, slots=True, repr=False)
class _UntrustedDocumentContent:
    """Document text structurally confined to an untrusted data member."""

    text: str = field(repr=False)
    trust_classification: str = field(
        default=UNTRUSTED_DOCUMENT_CONTENT,
        init=False,
        repr=False,
    )


@dataclass(frozen=True, slots=True, repr=False)
class _InternalAuthoritativeRetrievalRecord:
    """Minimal non-public record materialized before final transaction commit."""

    trusted: _TrustedAuthoritativeProvenance = field(repr=False)
    document_content: _UntrustedDocumentContent = field(repr=False)


CandidateBatch = tuple[UUID, ...]


class FinalAuthoritativeLoader(Protocol):
    """Provider-neutral final authorization and authoritative loading port."""

    async def load_authoritative_records(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        candidate_batches: tuple[CandidateBatch, ...],
    ) -> tuple[_InternalAuthoritativeRetrievalRecord, ...]: ...


class FinalCandidateValidatorLoader:
    """Bound, canonicalize, and validate final candidate identities."""

    def __init__(self, loader: FinalAuthoritativeLoader) -> None:
        self._loader = loader

    async def validate_and_load(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        candidate_ids: Sequence[UUID],
    ) -> tuple[_InternalAuthoritativeRetrievalRecord, ...]:
        """Always reauthorize, including the authorized-empty path."""
        batches = _canonical_candidate_batches(candidate_ids)
        return await self._loader.load_authoritative_records(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            candidate_batches=batches,
        )


def _canonical_candidate_batches(
    candidate_ids: Sequence[UUID],
) -> tuple[CandidateBatch, ...]:
    if any(not isinstance(candidate_id, UUID) for candidate_id in candidate_ids):
        raise TypeError("Final candidates must be UUID values.")
    ordered = tuple(sorted(set(candidate_ids)))
    if len(ordered) > MAX_FINAL_CANDIDATES:
        raise FinalCandidateLimitError(f"Final candidate count exceeds {MAX_FINAL_CANDIDATES}.")
    return tuple(
        ordered[offset : offset + FINAL_VALIDATION_BATCH_SIZE]
        for offset in range(0, len(ordered), FINAL_VALIDATION_BATCH_SIZE)
    )


@dataclass(frozen=True, slots=True)
class KeywordCandidate:
    """One scoped authoritative chunk identity and its one-based source rank."""

    chunk_id: UUID = field(repr=False)
    keyword_rank: int

    def __post_init__(self) -> None:
        if self.keyword_rank < 1:
            raise ValueError("keyword_rank must be positive")


@dataclass(frozen=True, slots=True)
class ScopedKeywordResult:
    """Validated request plus bounded keyword candidates for the next AF-3A slice."""

    request: RetrievalRequest
    candidates: tuple[KeywordCandidate, ...]


class RetrievalAccessPort(Protocol):
    """Two separately resourced PostgreSQL operations required by AF-3A-03."""

    async def verify_initial_access(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
    ) -> None: ...

    async def scoped_keyword_candidates(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        normalized_query: str,
    ) -> Sequence[KeywordCandidate]: ...


class ScopedKeywordRetrievalService:
    """Enforce initial access, pure validation, and scoped keyword ordering."""

    def __init__(self, access: RetrievalAccessPort) -> None:
        self._access = access

    async def retrieve(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        payload: Mapping[object, object],
    ) -> ScopedKeywordResult:
        """Return bounded keyword identities without retaining a database resource."""
        await self._access.verify_initial_access(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
        )
        request = parse_retrieval_request(payload)
        candidates = tuple(
            await self._access.scoped_keyword_candidates(
                proof=proof,
                knowledge_base_id=knowledge_base_id,
                normalized_query=request.normalized_query,
            )
        )
        return ScopedKeywordResult(request=request, candidates=candidates)
