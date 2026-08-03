"""Unit tests for AF-3A-03 provider-independent orchestration."""

import logging
from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest
from tests.retrieval_security import (
    AF3A03_CANONICAL_TUPLES,
    CanonicalAcceptanceTuple,
    acceptance_tuple,
    arm_r24_log_capture,
    assert_r24_sidecar,
)

from app.retrieval.domain import RetrievalRequestValidationError
from app.retrieval.service import (
    KeywordCandidate,
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    ScopedKeywordRetrievalService,
)
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal

_SCOPED_REPOSITORY_UNIT = acceptance_tuple(
    "RET-KEY-004",
    "AF3A-SCOPED-REPOSITORY-ONLY",
    "unit",
)


def _empty_r24_sink_matrix() -> dict[str, object]:
    return {
        "exception_error_records": (),
        "trace_span_names_attributes_status_events": (),
        "postgres_sql_database_driver_transaction_diagnostics": (),
        "service_diagnostics": (),
        "internal_authoritative_retrieval_record_diagnostics": (),
    }


def _proof() -> SessionAuthenticationProof:
    return SessionAuthenticationProof(
        principal=Principal(
            user_id=uuid4(),
            email="member@example.com",
            session_id=uuid4(),
        ),
        session_token_sha256="a" * 64,
    )


def _service_r24_sentinels(
    *,
    proof: SessionAuthenticationProof,
    knowledge_base_id: UUID,
    raw_query: str,
    normalized_query: str,
    candidate: KeywordCandidate,
) -> tuple[str, ...]:
    return (
        str(proof.principal.user_id),
        str(proof.principal.session_id),
        proof.session_token_sha256,
        str(knowledge_base_id),
        raw_query,
        normalized_query,
        str(candidate.chunk_id),
    )


class _FakeRetrievalAccess:
    def __init__(self, candidates: tuple[KeywordCandidate, ...] = ()) -> None:
        self.candidates = candidates
        self.calls: list[tuple[str, object, UUID, str | None]] = []
        self.initial_error: Exception | None = None

    async def verify_initial_access(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
    ) -> None:
        self.calls.append(("initial", proof, knowledge_base_id, None))
        if self.initial_error is not None:
            raise self.initial_error

    async def scoped_keyword_candidates(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        normalized_query: str,
    ) -> tuple[KeywordCandidate, ...]:
        self.calls.append(("keyword", proof, knowledge_base_id, normalized_query))
        return self.candidates


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_SCOPED_REPOSITORY_UNIT, id=_SCOPED_REPOSITORY_UNIT.pytest_id)],
)
async def test_service_preserves_proof_scope_order_and_normalized_bind(
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    proof = _proof()
    knowledge_base_id = uuid4()
    candidate = KeywordCandidate(chunk_id=uuid4(), keyword_rank=1)
    access = _FakeRetrievalAccess((candidate,))
    raw_query = "  Cafe\u0301\tMiXeD  "

    result = await ScopedKeywordRetrievalService(access).retrieve(
        proof=proof,
        knowledge_base_id=knowledge_base_id,
        payload={"query": raw_query, "requested_count": 1},
    )

    assert access.calls == [
        ("initial", proof, knowledge_base_id, None),
        ("keyword", proof, knowledge_base_id, "Café MiXeD"),
    ]
    assert result.request.normalized_query == "Café MiXeD"
    assert result.request.requested_count == 1
    assert result.candidates == (candidate,)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=_service_r24_sentinels(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            raw_query=raw_query,
            normalized_query=result.request.normalized_query,
            candidate=candidate,
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": (),
            "service_diagnostics": (repr(result), repr(candidate)),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "sentinel_field",
    [
        "user_id",
        "session_id",
        "session_token_sha256",
        "knowledge_base_id",
        "raw_query",
        "normalized_query",
        "chunk_id",
    ],
)
@pytest.mark.parametrize("leak_sink", ["application_log", "service_diagnostics"])
def test_service_r24_detects_each_reachable_sentinel_mutation(
    sentinel_field: str,
    leak_sink: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    proof = _proof()
    knowledge_base_id = uuid4()
    candidate = KeywordCandidate(chunk_id=uuid4(), keyword_rank=1)
    raw_query = "\u00a0R24-query-43d2856f-e\u0301\tpayload\u3000"
    normalized_query = "R24-query-43d2856f-é payload"
    sentinels_by_field = dict(
        zip(
            (
                "user_id",
                "session_id",
                "session_token_sha256",
                "knowledge_base_id",
                "raw_query",
                "normalized_query",
                "chunk_id",
            ),
            _service_r24_sentinels(
                proof=proof,
                knowledge_base_id=knowledge_base_id,
                raw_query=raw_query,
                normalized_query=normalized_query,
                candidate=candidate,
            ),
            strict=True,
        )
    )
    leaked_sentinel = sentinels_by_field[sentinel_field]
    sinks = _empty_r24_sink_matrix()
    if leak_sink == "application_log":
        logging.getLogger("tests.retrieval.r24").info("unsafe=%s", leaked_sentinel)
    else:
        sinks["service_diagnostics"] = {sentinel_field: leaked_sentinel}

    with pytest.raises(AssertionError, match="leaked a sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=tuple(sentinels_by_field.values()),
            log_records=caplog.records,
            sinks=sinks,
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"query": "contains\u0000null"},
        {"query": "valid", "requested_count": 0},
        {"query": "valid", "requested_count": 51},
        {"query": "valid", "requested_count": True},
    ],
)
async def test_invalid_request_runs_initial_access_but_never_keyword(
    payload: dict[str, object],
) -> None:
    proof = _proof()
    knowledge_base_id = uuid4()
    access = _FakeRetrievalAccess()

    with pytest.raises(RetrievalRequestValidationError):
        await ScopedKeywordRetrievalService(access).retrieve(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            payload=payload,
        )

    assert access.calls == [("initial", proof, knowledge_base_id, None)]


@pytest.mark.parametrize(
    "error",
    [RetrievalAuthenticationError(), RetrievalTargetNotFoundError()],
)
async def test_initial_access_failure_stops_request_and_keyword_work(error: Exception) -> None:
    proof = _proof()
    knowledge_base_id = uuid4()
    access = _FakeRetrievalAccess()
    access.initial_error = error

    with pytest.raises(type(error), match=str(error)):
        await ScopedKeywordRetrievalService(access).retrieve(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            payload={"query": "valid"},
        )

    assert access.calls == [("initial", proof, knowledge_base_id, None)]


def test_keyword_candidate_and_result_values_are_immutable() -> None:
    candidate = KeywordCandidate(chunk_id=uuid4(), keyword_rank=1)

    with pytest.raises(FrozenInstanceError):
        candidate.keyword_rank = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="keyword_rank must be positive"):
        KeywordCandidate(chunk_id=uuid4(), keyword_rank=0)


def test_af3a03_canonical_tuple_inventory_is_exact() -> None:
    assert len(AF3A03_CANONICAL_TUPLES) == 27
    assert sum(row.boundary == "AF3A_INITIAL_ACCESS" for row in AF3A03_CANONICAL_TUPLES) == 12
    assert sum(row.boundary == "AF3A_KEYWORD" for row in AF3A03_CANONICAL_TUPLES) == 15
    assert sum(row.test_level == "unit" for row in AF3A03_CANONICAL_TUPLES) == 2
    assert sum(row.test_level == "PostgreSQL integration" for row in AF3A03_CANONICAL_TUPLES) == 25


@pytest.mark.parametrize(
    "sink_name,sink_value",
    [
        ("trace_span_names_attributes_status_events", {"event": ["private-sentinel"]}),
        ("postgres_sql_database_driver_transaction_diagnostics", b"private-sentinel"),
        ("exception_error_records", RuntimeError("prefix-private-sentinel-suffix")),
        ("service_diagnostics", {"nested": "prefix-private-sentinel-suffix"}),
        (
            "internal_authoritative_retrieval_record_diagnostics",
            ("private-sentinel",),
        ),
    ],
)
def test_r24_scanner_rejects_exact_substring_and_recursive_leaks(
    sink_name: str,
    sink_value: object,
) -> None:
    sinks = _empty_r24_sink_matrix()
    sinks[sink_name] = sink_value
    with pytest.raises(AssertionError, match="leaked a sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=("private-sentinel",),
            log_records=(),
            sinks=sinks,
        )


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO])
def test_r24_capture_rejects_lower_level_application_log_leaks(
    level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinel = "lower-level-log-sentinel-753f8948"
    arm_r24_log_capture(caplog)

    logging.getLogger("tests.retrieval.r24").log(level, "prefix-%s-suffix", sentinel)

    with pytest.raises(AssertionError, match="leaked a sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=(sentinel,),
            log_records=caplog.records,
            sinks=_empty_r24_sink_matrix(),
        )


@pytest.mark.parametrize("placement", ["key", "nested-value"])
def test_r24_capture_rejects_structured_log_extra_leaks(
    placement: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinel = "structured-extra-sentinel-55f22d1b"
    arm_r24_log_capture(caplog)
    structured_extra = (
        {sentinel: {"safe": "safe"}}
        if placement == "key"
        else {"structured_payload": {"nested": f"prefix-{sentinel}-suffix"}}
    )

    logging.getLogger("tests.retrieval.r24").info("safe-event", extra=structured_extra)

    assert sentinel in repr(caplog.records[-1].__dict__)
    with pytest.raises(AssertionError, match="leaked a sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=(sentinel,),
            log_records=caplog.records,
            sinks=_empty_r24_sink_matrix(),
        )


@pytest.mark.parametrize("chain_kind", ["cause", "context"])
def test_r24_scanner_rejects_nested_exception_chain_leaks(chain_kind: str) -> None:
    sentinel = "exception-chain-sentinel-caa83493"
    try:
        raise RuntimeError(sentinel)
    except RuntimeError as inner:
        try:
            if chain_kind == "cause":
                raise RetrievalAuthenticationError from inner
            raise RetrievalAuthenticationError from None
        except RetrievalAuthenticationError as outer:
            captured = outer

    with pytest.raises(AssertionError, match="leaked a sentinel"):
        sinks = _empty_r24_sink_matrix()
        sinks["exception_error_records"] = captured
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=(sentinel,),
            log_records=(),
            sinks=sinks,
        )


def test_r24_scanner_rejects_nested_exception_attribute_leaks() -> None:
    sentinel = "exception-attribute-sentinel-62418e38"
    captured = RuntimeError("safe")
    captured.private_detail = {"nested": f"prefix-{sentinel}-suffix"}  # type: ignore[attr-defined]
    sinks = _empty_r24_sink_matrix()
    sinks["exception_error_records"] = captured

    with pytest.raises(AssertionError, match="leaked a sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=(sentinel,),
            log_records=(),
            sinks=sinks,
        )


def test_r24_sidecar_requires_every_owned_sink_registration() -> None:
    sinks = _empty_r24_sink_matrix()
    del sinks["postgres_sql_database_driver_transaction_diagnostics"]

    with pytest.raises(AssertionError, match="must explicitly register every owned sink"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=("registration-sentinel-4f49ec0d",),
            log_records=(),
            sinks=sinks,
        )


def test_r24_sidecar_requires_at_least_one_sentinel() -> None:
    with pytest.raises(AssertionError, match="at least one sentinel"):
        assert_r24_sidecar(
            _SCOPED_REPOSITORY_UNIT,
            sentinels=(),
            log_records=(),
            sinks=_empty_r24_sink_matrix(),
        )
