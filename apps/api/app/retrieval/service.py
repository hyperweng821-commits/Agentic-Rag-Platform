"""Provider-independent AF-3A retrieval access and keyword orchestration."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol
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
