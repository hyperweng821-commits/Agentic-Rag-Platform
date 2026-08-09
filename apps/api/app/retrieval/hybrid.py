"""Bounded AF-3B hybrid retrieval orchestration and exact RRF."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final
from uuid import UUID

from app.ingestion.embeddings import EmbeddingError, EmbeddingModel, EmbeddingVector
from app.retrieval.chroma import (
    DenseProviderError,
    DenseRetrievalPort,
    _DenseProviderResult,
)
from app.retrieval.service import (
    FinalCandidateValidatorLoader,
    KeywordCandidate,
    RetrievalUnavailableError,
    ScopedKeywordRetrievalService,
    _InternalAuthoritativeRetrievalRecord,
)
from app.security.authentication import SessionAuthenticationProof

DENSE_OVERFETCH_FACTOR: Final = 4
MAX_DENSE_CANDIDATES: Final = 128
MAX_PROVIDER_CANDIDATES: Final = 128
MAX_KEYWORD_CANDIDATES: Final = 128
MAX_UNIQUE_CANDIDATES: Final = 192
RRF_K: Final = 60


@dataclass(frozen=True, slots=True, repr=False)
class _FusedInternalAuthoritativeRetrievalRecord:
    """One authoritative AF-3A record plus bounded deterministic AF-3B ranks."""

    authoritative: _InternalAuthoritativeRetrievalRecord = field(repr=False)
    keyword_rank: int | None
    dense_rank: int | None
    fused_numerator: int
    fused_denominator: int
    fused_rank: int


@dataclass(frozen=True, slots=True, repr=False)
class HybridRetrievalResult:
    """Non-public AF-3B result with no rejected-candidate diagnostics."""

    records: tuple[_FusedInternalAuthoritativeRetrievalRecord, ...] = field(repr=False)


def configured_provider_count(requested_count: int) -> int:
    """Return the exact checked AF-3B dense over-fetch count."""
    if type(requested_count) is not int or not 1 <= requested_count <= 50:
        raise ValueError("requested_count is outside the validated domain")
    return min(
        MAX_PROVIDER_CANDIDATES,
        MAX_DENSE_CANDIDATES,
        requested_count * DENSE_OVERFETCH_FACTOR,
    )


def _validate_query_embedding(vectors: object, *, dimension: int) -> EmbeddingVector:
    if type(vectors) is not list or len(vectors) != 1:
        raise RetrievalUnavailableError
    vector = vectors[0]
    if type(vector) not in {list, tuple} or len(vector) != dimension:
        raise RetrievalUnavailableError
    if any(type(value) is not float or not math.isfinite(value) for value in vector):
        raise RetrievalUnavailableError
    return tuple(vector)


def _keyword_rank_map(candidates: Sequence[KeywordCandidate]) -> dict[UUID, int]:
    if len(candidates) > MAX_KEYWORD_CANDIDATES:
        raise RetrievalUnavailableError
    ranks: dict[UUID, int] = {}
    for candidate in candidates:
        if (
            not isinstance(candidate, KeywordCandidate)
            or not isinstance(candidate.chunk_id, UUID)
            or type(candidate.keyword_rank) is not int
            or not 1 <= candidate.keyword_rank <= MAX_KEYWORD_CANDIDATES
        ):
            raise RetrievalUnavailableError
        previous = ranks.get(candidate.chunk_id)
        if previous is None or candidate.keyword_rank < previous:
            ranks[candidate.chunk_id] = candidate.keyword_rank
    return ranks


def dense_rank_map(
    result: _DenseProviderResult,
    *,
    configured_count: int,
) -> dict[UUID, int]:
    """Validate the bounded typed-provider result and preserve absolute ranks."""
    if (
        not isinstance(result, _DenseProviderResult)
        or type(result.position_count) is not int
        or not 0 <= result.position_count <= configured_count
        or result.position_count > MAX_PROVIDER_CANDIDATES
    ):
        raise DenseProviderError
    return dict(result._ranked_chunk_ids)


def _rrf_score(keyword_rank: int | None, dense_rank: int | None) -> Fraction:
    if keyword_rank is None and dense_rank is None:
        raise ValueError("At least one source rank is required.")
    score = Fraction(0, 1)
    if keyword_rank is not None:
        score += Fraction(1, RRF_K + keyword_rank)
    if dense_rank is not None:
        score += Fraction(1, RRF_K + dense_rank)
    return score


def fuse_authoritative_records(
    records: Sequence[_InternalAuthoritativeRetrievalRecord],
    *,
    keyword_ranks: Mapping[UUID, int],
    dense_ranks: Mapping[UUID, int],
    requested_count: int,
) -> tuple[_FusedInternalAuthoritativeRetrievalRecord, ...]:
    """Apply exact RRF and the complete deterministic tie order."""
    if type(requested_count) is not int or not 1 <= requested_count <= 50:
        raise ValueError("requested_count is outside the validated domain")
    by_chunk: dict[UUID, _InternalAuthoritativeRetrievalRecord] = {}
    for record in records:
        chunk_id = record.trusted.chunk_id
        if chunk_id in by_chunk or (chunk_id not in keyword_ranks and chunk_id not in dense_ranks):
            raise RetrievalUnavailableError
        by_chunk[chunk_id] = record

    scored: list[
        tuple[
            Fraction,
            int,
            int,
            int,
            UUID,
            _InternalAuthoritativeRetrievalRecord,
            int | None,
            int | None,
        ]
    ] = []
    absent_rank = MAX_PROVIDER_CANDIDATES + 1
    for chunk_id, record in by_chunk.items():
        keyword_rank = keyword_ranks.get(chunk_id)
        dense_rank = dense_ranks.get(chunk_id)
        score = _rrf_score(keyword_rank, dense_rank)
        contributing = tuple(rank for rank in (keyword_rank, dense_rank) if rank is not None)
        scored.append(
            (
                score,
                min(contributing),
                absent_rank if keyword_rank is None else keyword_rank,
                absent_rank if dense_rank is None else dense_rank,
                chunk_id,
                record,
                keyword_rank,
                dense_rank,
            )
        )
    scored.sort(key=lambda item: (-item[0], item[1], item[2], item[3], item[4]))
    return tuple(
        _FusedInternalAuthoritativeRetrievalRecord(
            authoritative=item[5],
            keyword_rank=item[6],
            dense_rank=item[7],
            fused_numerator=item[0].numerator,
            fused_denominator=item[0].denominator,
            fused_rank=fused_rank,
        )
        for fused_rank, item in enumerate(scored[:requested_count], start=1)
    )


class HybridRetrievalService:
    """Compose the existing AF-3A boundaries with required AF-3B Provider work."""

    def __init__(
        self,
        *,
        keyword_service: ScopedKeywordRetrievalService,
        embedding_model: EmbeddingModel,
        dense_retrieval: DenseRetrievalPort,
        final_validator: FinalCandidateValidatorLoader,
    ) -> None:
        if type(embedding_model.dimension) is not int or embedding_model.dimension <= 0:
            raise ValueError("Embedding dimension must be a positive integer.")
        self._keyword_service = keyword_service
        self._embedding_model = embedding_model
        self._dense_retrieval = dense_retrieval
        self._final_validator = final_validator

    async def retrieve(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        payload: Mapping[object, object],
    ) -> HybridRetrievalResult:
        scoped = await self._keyword_service.retrieve(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            payload=payload,
        )
        keyword_ranks = _keyword_rank_map(scoped.candidates)
        try:
            raw_vectors = await self._embedding_model.embed([scoped.request.normalized_query])
            embedding = _validate_query_embedding(
                raw_vectors,
                dimension=self._embedding_model.dimension,
            )
            provider_count = configured_provider_count(scoped.request.requested_count)
            dense_result = await self._dense_retrieval.query(
                embedding=embedding,
                knowledge_base_id=knowledge_base_id,
                candidate_count=provider_count,
            )
            dense_ranks = dense_rank_map(dense_result, configured_count=provider_count)
        except (EmbeddingError, DenseProviderError):
            raise RetrievalUnavailableError from None

        union = set(keyword_ranks) | set(dense_ranks)
        if len(union) > MAX_UNIQUE_CANDIDATES:
            raise RetrievalUnavailableError
        authoritative = await self._final_validator.validate_and_load(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            candidate_ids=tuple(union),
        )
        authoritative_ids = {record.trusted.chunk_id for record in authoritative}
        if len(authoritative_ids) != len(authoritative) or not authoritative_ids <= union:
            raise RetrievalUnavailableError
        records = fuse_authoritative_records(
            authoritative,
            keyword_ranks=keyword_ranks,
            dense_ranks=dense_ranks,
            requested_count=scoped.request.requested_count,
        )
        return HybridRetrievalResult(records=records)
