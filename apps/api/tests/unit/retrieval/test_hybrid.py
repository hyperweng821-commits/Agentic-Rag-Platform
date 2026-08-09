"""Focused vertical tests for AF-3B hybrid orchestration and exact RRF."""

import hashlib
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from app.ingestion.embeddings import EmbeddingRequestError
from app.retrieval import hybrid as hybrid_module
from app.retrieval.chroma import (
    DenseProviderError,
)
from app.retrieval.chroma import (
    _DenseProviderResult as DenseProviderResult,
)
from app.retrieval.hybrid import (
    RRF_K,
    HybridRetrievalService,
    configured_provider_count,
    dense_rank_map,
    fuse_authoritative_records,
)
from app.retrieval.service import (
    FinalCandidateValidatorLoader,
    KeywordCandidate,
    RetrievalUnavailableError,
    ScopedKeywordRetrievalService,
    _InternalAuthoritativeRetrievalRecord,
    _TrustedAuthoritativeProvenance,
    _UntrustedDocumentContent,
)
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal


def _proof() -> SessionAuthenticationProof:
    return SessionAuthenticationProof(
        principal=Principal(user_id=uuid4(), email="member@example.com", session_id=uuid4()),
        session_token_sha256="a" * 64,
    )


def _record(chunk_id: UUID) -> _InternalAuthoritativeRetrievalRecord:
    text = f"authoritative-{chunk_id}"
    return _InternalAuthoritativeRetrievalRecord(
        trusted=_TrustedAuthoritativeProvenance(
            knowledge_base_id=uuid5(chunk_id, "kb"),
            document_id=uuid5(chunk_id, "document"),
            chunk_id=chunk_id,
            content_sha256=hashlib.sha256(text.encode()).hexdigest(),
            source_display_name="source.txt",
            page_start=None,
            page_end=None,
            character_start=0,
            character_end=len(text),
        ),
        document_content=_UntrustedDocumentContent(text=text),
    )


class _Access:
    def __init__(self, candidates: tuple[KeywordCandidate, ...], ledger: list[str]) -> None:
        self.candidates = candidates
        self.ledger = ledger

    async def verify_initial_access(self, **kwargs: object) -> None:
        self.ledger.append("initial")

    async def scoped_keyword_candidates(self, **kwargs: object) -> tuple[KeywordCandidate, ...]:
        self.ledger.append("keyword")
        return self.candidates


class _Embedding:
    model_id = "fake"
    dimension = 4

    def __init__(self, ledger: list[str], result: object | None = None) -> None:
        self.ledger = ledger
        self.result = result if result is not None else [(0.25, -0.5, 0.0, 1.0)]
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> object:
        self.ledger.append("embedding")
        self.calls.append(texts)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    async def close(self) -> None:
        pass


class _Dense:
    def __init__(self, ledger: list[str], result: DenseProviderResult | Exception) -> None:
        self.ledger = ledger
        self.result = result
        self.calls: list[tuple[tuple[float, ...], UUID, int]] = []

    async def query(
        self,
        *,
        embedding: tuple[float, ...],
        knowledge_base_id: UUID,
        candidate_count: int,
    ) -> DenseProviderResult:
        self.ledger.append("dense")
        self.calls.append((embedding, knowledge_base_id, candidate_count))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _Loader:
    def __init__(
        self,
        ledger: list[str],
        authoritative_ids: set[UUID] | None = None,
    ) -> None:
        self.ledger = ledger
        self.authoritative_ids = authoritative_ids
        self.calls: list[tuple[tuple[UUID, ...], ...]] = []

    async def load_authoritative_records(
        self,
        *,
        candidate_batches: tuple[tuple[UUID, ...], ...],
        **kwargs: object,
    ) -> tuple[_InternalAuthoritativeRetrievalRecord, ...]:
        self.ledger.append("final")
        self.calls.append(candidate_batches)
        candidate_ids = tuple(candidate for batch in candidate_batches for candidate in batch)
        selected = (
            candidate_ids
            if self.authoritative_ids is None
            else tuple(item for item in candidate_ids if item in self.authoritative_ids)
        )
        return tuple(_record(candidate_id) for candidate_id in reversed(selected))


def _dense_result(*chunk_ids: UUID) -> DenseProviderResult:
    return DenseProviderResult(
        position_count=len(chunk_ids),
        candidates=tuple(
            (f"chunk:{chunk_id}", float(index), index) for index, chunk_id in enumerate(chunk_ids)
        ),
    )


async def test_vertical_pipeline_is_ordered_and_calls_embedding_exactly_once() -> None:
    ledger: list[str] = []
    overlap = uuid4()
    keyword_only = uuid4()
    dense_only = uuid4()
    embedding = _Embedding(ledger)
    dense = _Dense(ledger, _dense_result(overlap, dense_only))
    loader = _Loader(ledger)
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(
            _Access(
                (
                    KeywordCandidate(chunk_id=keyword_only, keyword_rank=1),
                    KeywordCandidate(chunk_id=overlap, keyword_rank=2),
                ),
                ledger,
            )
        ),
        embedding_model=embedding,  # type: ignore[arg-type]
        dense_retrieval=dense,
        final_validator=FinalCandidateValidatorLoader(loader),
    )
    proof = _proof()
    knowledge_base_id = uuid4()

    result = await service.retrieve(
        proof=proof,
        knowledge_base_id=knowledge_base_id,
        payload={"query": "  hybrid\tquery  ", "requested_count": 10},
    )

    assert ledger == ["initial", "keyword", "embedding", "dense", "final"]
    assert embedding.calls == [["hybrid query"]]
    assert dense.calls == [((0.25, -0.5, 0.0, 1.0), knowledge_base_id, 40)]
    assert tuple(len(batch) for batch in loader.calls[0]) == (3,)
    by_id = {item.authoritative.trusted.chunk_id: item for item in result.records}
    assert by_id[overlap].keyword_rank == 2
    assert by_id[overlap].dense_rank == 1
    assert by_id[keyword_only].dense_rank is None
    assert by_id[dense_only].keyword_rank is None
    assert not hasattr(result, "removed_candidate_ids")


async def test_stale_dense_candidate_is_removed_without_backfill() -> None:
    ledger: list[str] = []
    stale = uuid4()
    retained = uuid4()
    loader = _Loader(ledger, {retained})
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(_Access((), ledger)),
        embedding_model=_Embedding(ledger),  # type: ignore[arg-type]
        dense_retrieval=_Dense(ledger, _dense_result(stale, retained)),
        final_validator=FinalCandidateValidatorLoader(loader),
    )

    result = await service.retrieve(
        proof=_proof(),
        knowledge_base_id=uuid4(),
        payload={"query": "query", "requested_count": 2},
    )

    assert [item.authoritative.trusted.chunk_id for item in result.records] == [retained]
    assert result.records[0].dense_rank == 2
    assert not hasattr(result, "removed_candidate_ids")
    assert str(stale) not in repr(result)


async def test_present_empty_sources_still_run_final_reauthorization() -> None:
    ledger: list[str] = []
    loader = _Loader(ledger)
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(_Access((), ledger)),
        embedding_model=_Embedding(ledger),  # type: ignore[arg-type]
        dense_retrieval=_Dense(ledger, _dense_result()),
        final_validator=FinalCandidateValidatorLoader(loader),
    )

    result = await service.retrieve(
        proof=_proof(),
        knowledge_base_id=uuid4(),
        payload={"query": "query"},
    )

    assert result.records == ()
    assert not hasattr(result, "removed_candidate_ids")
    assert loader.calls == [()]
    assert ledger[-1] == "final"


@pytest.mark.parametrize(
    "vectors",
    [
        [],
        [(0.25, -0.5, 0.0)],
        [(0.25, -0.5, 0, 1.0)],
        [(0.25, -0.5, float("nan"), 1.0)],
        [(0.25, -0.5, 0.0, 1.0), (0.25, -0.5, 0.0, 1.0)],
    ],
)
async def test_invalid_embedding_result_stops_before_chroma_and_final(vectors: object) -> None:
    ledger: list[str] = []
    dense = _Dense(ledger, _dense_result())
    loader = _Loader(ledger)
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(_Access((), ledger)),
        embedding_model=_Embedding(ledger, vectors),  # type: ignore[arg-type]
        dense_retrieval=dense,
        final_validator=FinalCandidateValidatorLoader(loader),
    )

    with pytest.raises(RetrievalUnavailableError):
        await service.retrieve(
            proof=_proof(),
            knowledge_base_id=uuid4(),
            payload={"query": "query"},
        )

    assert dense.calls == []
    assert loader.calls == []


@pytest.mark.parametrize(("dense_count", "succeeds"), [(64, True), (65, False)])
async def test_unique_union_accepts_192_and_rejects_193_before_final_sql(
    dense_count: int,
    succeeds: bool,
) -> None:
    ledger: list[str] = []
    keyword_ids = tuple(uuid5(NAMESPACE_URL, f"keyword-{index}") for index in range(128))
    dense_ids = tuple(uuid5(NAMESPACE_URL, f"dense-{index}") for index in range(dense_count))
    loader = _Loader(ledger)
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(
            _Access(
                tuple(
                    KeywordCandidate(chunk_id=chunk_id, keyword_rank=index + 1)
                    for index, chunk_id in enumerate(keyword_ids)
                ),
                ledger,
            )
        ),
        embedding_model=_Embedding(ledger),  # type: ignore[arg-type]
        dense_retrieval=_Dense(ledger, _dense_result(*dense_ids)),
        final_validator=FinalCandidateValidatorLoader(loader),
    )
    operation = service.retrieve(
        proof=_proof(),
        knowledge_base_id=uuid4(),
        payload={"query": "query", "requested_count": 50},
    )

    if succeeds:
        result = await operation
        assert len(result.records) == 50
        assert tuple(len(batch) for batch in loader.calls[0]) == (64, 64, 64)
    else:
        with pytest.raises(RetrievalUnavailableError):
            await operation
        assert loader.calls == []


@pytest.mark.parametrize(
    "provider_failure",
    [EmbeddingRequestError("private detail"), DenseProviderError()],
)
async def test_required_provider_failure_discards_keyword_and_skips_final(
    provider_failure: Exception,
) -> None:
    ledger: list[str] = []
    keyword_id = uuid4()
    loader = _Loader(ledger)
    embedding_result: object = (
        provider_failure if isinstance(provider_failure, EmbeddingRequestError) else None
    )
    dense_result: DenseProviderResult | Exception = (
        provider_failure if isinstance(provider_failure, DenseProviderError) else _dense_result()
    )
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(
            _Access((KeywordCandidate(chunk_id=keyword_id, keyword_rank=1),), ledger)
        ),
        embedding_model=_Embedding(ledger, embedding_result),  # type: ignore[arg-type]
        dense_retrieval=_Dense(ledger, dense_result),
        final_validator=FinalCandidateValidatorLoader(loader),
    )

    with pytest.raises(RetrievalUnavailableError) as captured:
        await service.retrieve(
            proof=_proof(),
            knowledge_base_id=uuid4(),
            payload={"query": "query"},
        )

    assert str(captured.value) == "Retrieval is unavailable."
    assert loader.calls == []
    assert "final" not in ledger


def test_dense_candidate_validation_preserves_positions_and_earliest_duplicate() -> None:
    chunk_id = uuid4()
    result = DenseProviderResult(
        position_count=5,
        candidates=(
            ("malformed", 0.1, 0),
            (f"chunk:{chunk_id}", 0.2, 1),
            (f"chunk:{chunk_id}", 0.3, 2),
            (f"chunk:{uuid4()}".upper(), 0.4, 3),
            (f"chunk:{uuid4()}", float("nan"), 4),
        ),
    )

    assert dense_rank_map(result, configured_count=8) == {chunk_id: 2}


def test_typed_adapter_none_score_remains_a_valid_ranked_candidate() -> None:
    first = uuid4()
    second = uuid4()
    result = DenseProviderResult(
        position_count=2,
        candidates=(
            (f"chunk:{first}", None, 0),
            (f"chunk:{second}", 0.2, 1),
        ),
    )

    assert dense_rank_map(result, configured_count=4) == {first: 1, second: 2}


@pytest.mark.parametrize(
    "position_count,candidates",
    [
        (2, ()),
        (
            2,
            (
                (f"chunk:{uuid4()}", 0.1, 0),
                (f"chunk:{uuid4()}", 0.2, 0),
            ),
        ),
        (1, (("x" * 129, 0.1, 0),)),
    ],
)
def test_malformed_typed_provider_result_fails_closed(
    position_count: int,
    candidates: tuple[tuple[object, object, int], ...],
) -> None:
    with pytest.raises(DenseProviderError):
        DenseProviderResult(position_count=position_count, candidates=candidates)


def test_exact_rrf_collision_uses_complete_tie_order() -> None:
    rank_3_80 = uuid5(NAMESPACE_URL, "rank-3-80")
    rank_24_30 = uuid5(NAMESPACE_URL, "rank-24-30")
    fused = fuse_authoritative_records(
        (_record(rank_24_30), _record(rank_3_80)),
        keyword_ranks={rank_3_80: 3, rank_24_30: 24},
        dense_ranks={rank_3_80: 80, rank_24_30: 30},
        requested_count=2,
    )

    assert RRF_K == 60
    assert [(item.fused_numerator, item.fused_denominator) for item in fused] == [
        (29, 1260),
        (29, 1260),
    ]
    assert [item.authoritative.trusted.chunk_id for item in fused] == [rank_3_80, rank_24_30]
    assert [item.fused_rank for item in fused] == [1, 2]


def test_requested_count_is_applied_after_stable_exact_sort() -> None:
    ids = tuple(uuid5(NAMESPACE_URL, f"cutoff-{index}") for index in range(4))
    fused = fuse_authoritative_records(
        tuple(_record(chunk_id) for chunk_id in reversed(ids)),
        keyword_ranks={chunk_id: index + 1 for index, chunk_id in enumerate(ids)},
        dense_ranks={},
        requested_count=2,
    )
    assert [item.authoritative.trusted.chunk_id for item in fused] == list(ids[:2])
    assert [item.fused_rank for item in fused] == [1, 2]


@pytest.mark.parametrize(("requested_count", "expected"), [(1, 4), (10, 40), (32, 128), (50, 128)])
def test_configured_provider_count_formula(requested_count: int, expected: int) -> None:
    assert configured_provider_count(requested_count) == expected


@pytest.mark.parametrize("requested_count", [0, 51, True])
def test_configured_provider_count_rejects_unvalidated_values(requested_count: object) -> None:
    with pytest.raises(ValueError, match="validated domain"):
        configured_provider_count(requested_count)  # type: ignore[arg-type]


def test_exact_rrf_requires_at_least_one_source_rank() -> None:
    with pytest.raises(ValueError, match="source rank"):
        hybrid_module._rrf_score(None, None)


@pytest.mark.parametrize("requested_count", [0, 51, True])
def test_fusion_rejects_unvalidated_cutoff(requested_count: object) -> None:
    with pytest.raises(ValueError, match="validated domain"):
        fuse_authoritative_records(
            (),
            keyword_ranks={},
            dense_ranks={},
            requested_count=requested_count,  # type: ignore[arg-type]
        )


def test_fusion_rejects_duplicate_or_unranked_authoritative_records() -> None:
    chunk_id = uuid4()
    record = _record(chunk_id)
    with pytest.raises(RetrievalUnavailableError):
        fuse_authoritative_records(
            (record, record),
            keyword_ranks={chunk_id: 1},
            dense_ranks={},
            requested_count=1,
        )
    with pytest.raises(RetrievalUnavailableError):
        fuse_authoritative_records(
            (record,),
            keyword_ranks={},
            dense_ranks={},
            requested_count=1,
        )


def test_hybrid_service_rejects_invalid_embedding_dimension() -> None:
    ledger: list[str] = []
    embedding = _Embedding(ledger)
    embedding.dimension = 0
    with pytest.raises(ValueError, match="dimension"):
        HybridRetrievalService(
            keyword_service=ScopedKeywordRetrievalService(_Access((), ledger)),
            embedding_model=embedding,  # type: ignore[arg-type]
            dense_retrieval=_Dense(ledger, _dense_result()),
            final_validator=FinalCandidateValidatorLoader(_Loader(ledger)),
        )


async def test_keyword_candidate_overflow_stops_before_provider_work() -> None:
    ledger: list[str] = []
    candidates = tuple(
        KeywordCandidate(chunk_id=uuid4(), keyword_rank=(index % 128) + 1) for index in range(129)
    )
    dense = _Dense(ledger, _dense_result())
    loader = _Loader(ledger)
    service = HybridRetrievalService(
        keyword_service=ScopedKeywordRetrievalService(_Access(candidates, ledger)),
        embedding_model=_Embedding(ledger),  # type: ignore[arg-type]
        dense_retrieval=dense,
        final_validator=FinalCandidateValidatorLoader(loader),
    )

    with pytest.raises(RetrievalUnavailableError):
        await service.retrieve(
            proof=_proof(),
            knowledge_base_id=uuid4(),
            payload={"query": "query"},
        )

    assert dense.calls == []
    assert loader.calls == []
