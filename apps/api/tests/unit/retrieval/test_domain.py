"""Unit tests for the pure AF-3A-1 retrieval request contract."""

from collections.abc import Iterator, Sequence
from logging import LogRecord
from types import MappingProxyType

import pytest
from tests.retrieval_security import (
    CanonicalAcceptanceTuple,
    arm_r24_log_capture,
    assert_r24_sidecar,
    pure_request_validator_remediation_tuple,
)

from app.retrieval.domain import (
    RetrievalRequest,
    RetrievalRequestValidationError,
    parse_retrieval_request,
)

_ADR_008_WHITESPACE_CODE_POINTS = (
    *range(0x0009, 0x000E),
    0x0020,
    0x0085,
    0x00A0,
    0x1680,
    *range(0x2000, 0x200B),
    0x2028,
    0x2029,
    0x202F,
    0x205F,
    0x3000,
)


class _StringSubclass(str):
    pass


class _IntegerSubclass(int):
    pass


class _DuckTypedMapping:
    def __iter__(self) -> Iterator[str]:
        return iter(("query",))

    def __getitem__(self, key: str) -> object:
        return "valid"

    def get(self, key: str, default: object = None) -> object:
        return "valid" if key == "query" else default


def _assert_pure_request_r24_sidecar(
    canonical_tuple: CanonicalAcceptanceTuple,
    *,
    sentinels: tuple[str | bytes, ...],
    log_records: Sequence[LogRecord],
    exception_error_records: object = (),
) -> None:
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=sentinels,
        log_records=log_records,
        sinks={
            "exception_error_records": exception_error_records,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": (),
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


def test_list_payload_is_rejected_with_validation_error() -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request(["query"])


def test_duck_typed_non_mapping_payload_is_rejected_with_validation_error() -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request(_DuckTypedMapping())


def test_dict_payload_is_accepted() -> None:
    assert parse_retrieval_request({"query": "valid"}) == RetrievalRequest(
        normalized_query="valid",
        requested_count=10,
    )


def test_missing_query_is_rejected() -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({})


def test_extra_field_is_rejected() -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": "valid", "extra": "not accepted"})


@pytest.mark.parametrize("alias", ["q", "text", "normalized_query", "limit", "count"])
def test_aliases_are_rejected(alias: str) -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": "valid", alias: "not accepted"})


def test_non_string_key_is_rejected() -> None:
    payload: dict[object, object] = {"query": "valid", 1: "not accepted"}

    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request(payload)


@pytest.mark.parametrize(
    "query",
    [
        pytest.param(None, id="null"),
        pytest.param(True, id="boolean"),
        pytest.param(1, id="integer"),
        pytest.param(1.0, id="float"),
        pytest.param(["query"], id="list"),
        pytest.param({"query": "value"}, id="mapping"),
        pytest.param(_StringSubclass("query"), id="string-subclass"),
    ],
)
def test_query_requires_exact_string_type(query: object) -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": query})


def test_requested_count_defaults_to_ten() -> None:
    request = parse_retrieval_request({"query": "valid"})

    assert request.requested_count == 10


@pytest.mark.parametrize("requested_count", [1, 50])
def test_requested_count_accepts_inclusive_boundaries(requested_count: int) -> None:
    request = parse_retrieval_request({"query": "valid", "requested_count": requested_count})

    assert request.requested_count == requested_count


@pytest.mark.parametrize(
    "requested_count",
    [
        pytest.param(-1, id="negative-one"),
        pytest.param(0, id="zero"),
        pytest.param(51, id="fifty-one"),
        pytest.param(True, id="boolean"),
        pytest.param(1.0, id="float"),
        pytest.param("1", id="string"),
        pytest.param(None, id="null"),
        pytest.param([1], id="list-container"),
        pytest.param({"count": 1}, id="mapping-container"),
        pytest.param((1,), id="tuple-container"),
        pytest.param(_IntegerSubclass(1), id="integer-subclass"),
    ],
)
def test_requested_count_rejects_invalid_values(
    requested_count: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    canonical_tuple = None
    if type(requested_count) is int and requested_count == -1:
        canonical_tuple = pure_request_validator_remediation_tuple(
            "RET-BND-003",
            "PARSER-NEGATIVE-ONE-REJECTED",
            "unit",
        )
        arm_r24_log_capture(caplog)

    with pytest.raises(RetrievalRequestValidationError) as exc_info:
        parse_retrieval_request({"query": "valid", "requested_count": requested_count})

    if canonical_tuple is not None:
        _assert_pure_request_r24_sidecar(
            canonical_tuple,
            sentinels=("-1",),
            log_records=caplog.records,
            exception_error_records=(exc_info.value,),
        )


def test_parser_accepts_runtime_mapping() -> None:
    payload = MappingProxyType({"query": "\u00a0valid\u3000", "requested_count": 1})

    assert parse_retrieval_request(payload) == RetrievalRequest(
        normalized_query="valid",
        requested_count=1,
    )


def test_canonically_equivalent_queries_produce_equal_nfc_requests() -> None:
    decomposed = parse_retrieval_request({"query": "e\u0301"})
    precomposed = parse_retrieval_request({"query": "\u00e9"})

    assert decomposed == precomposed
    assert decomposed.normalized_query == "\u00e9"


@pytest.mark.parametrize(
    "code_point",
    _ADR_008_WHITESPACE_CODE_POINTS,
    ids=lambda code_point: f"U+{code_point:04X}",
)
def test_every_adr_008_whitespace_code_point_is_trimmed_and_collapsed(
    code_point: int,
) -> None:
    whitespace = chr(code_point)
    query = f"{whitespace}{whitespace}alpha{whitespace}{whitespace}beta{whitespace}"

    request = parse_retrieval_request({"query": query})

    assert request.normalized_query == "alpha beta"


def test_excluded_whitespace_like_code_point_is_preserved() -> None:
    query = "\u200balpha\u200b\u200bbeta\u200b"

    assert parse_retrieval_request({"query": query}).normalized_query == query


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param(
            "AgentForge agentforge",
            "AgentForge agentforge",
            id="case",
        ),
        pytest.param("\uff21gent", "\uff21gent", id="compatibility-character"),
        pytest.param("Hello, world!?", "Hello, world!?", id="punctuation"),
    ],
)
def test_forbidden_transformations_are_not_applied(query: str, expected: str) -> None:
    assert parse_retrieval_request({"query": query}).normalized_query == expected


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("\u0000", id="single"),
        pytest.param("a\u0000b", id="embedded"),
    ],
)
def test_null_code_point_is_rejected(query: str) -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": query})


def test_adjacent_control_is_accepted_and_preserved() -> None:
    query = "a\u0001b"

    assert parse_retrieval_request({"query": query}).normalized_query == query


@pytest.mark.parametrize("scalar_count", [1, 2_048])
def test_normalized_scalar_boundaries_are_accepted(scalar_count: int) -> None:
    query = "a" * scalar_count

    assert len(parse_retrieval_request({"query": query}).normalized_query) == scalar_count


def test_post_normalization_scalar_boundary(
    caplog: pytest.LogCaptureFixture,
) -> None:
    canonical_tuple = pure_request_validator_remediation_tuple(
        "RET-BND-001",
        "POST-NORMALIZATION-SCALAR-BOUNDARY",
        "unit",
    )
    raw_query = "\t" + "a" * 2_048 + "\u3000"
    arm_r24_log_capture(caplog)

    request = parse_retrieval_request({"query": raw_query})

    assert request.normalized_query == "a" * 2_048
    assert len(request.normalized_query) == 2_048
    _assert_pure_request_r24_sidecar(
        canonical_tuple,
        sentinels=(raw_query,),
        log_records=caplog.records,
    )


def test_normalized_scalar_count_above_maximum_is_rejected() -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": "a" * 2_049})


def test_whitespace_only_query_is_rejected_after_normalization() -> None:
    query = "".join(chr(code_point) for code_point in _ADR_008_WHITESPACE_CODE_POINTS)

    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": query})


def test_4096_utf8_bytes_are_accepted() -> None:
    query = "\U0001f642" * 1_024

    request = parse_retrieval_request({"query": query})

    assert len(request.normalized_query.encode("utf-8")) == 4_096


def test_4097_utf8_bytes_are_rejected() -> None:
    query = "\U0001f642" * 1_024 + "a"

    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": query})


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("\ud800", id="high-surrogate"),
        pytest.param("\udc00", id="low-surrogate"),
    ],
)
def test_surrogates_are_rejected(query: str) -> None:
    with pytest.raises(RetrievalRequestValidationError):
        parse_retrieval_request({"query": query})


def test_validation_exception_does_not_disclose_query() -> None:
    private_fragment = "PRIVATE-QUERY-FRAGMENT"
    query = private_fragment + "a" * 2_049

    with pytest.raises(RetrievalRequestValidationError) as exc_info:
        parse_retrieval_request({"query": query})

    assert query not in str(exc_info.value)
    assert query not in repr(exc_info.value)
    assert private_fragment not in str(exc_info.value)
    assert private_fragment not in repr(exc_info.value)


def test_validation_exception_does_not_disclose_unknown_key() -> None:
    private_key = "PRIVATE-UNKNOWN-KEY"

    with pytest.raises(RetrievalRequestValidationError) as exc_info:
        parse_retrieval_request({"query": "valid", private_key: "value"})

    assert private_key not in str(exc_info.value)
    assert private_key not in repr(exc_info.value)


def test_retrieval_request_repr_does_not_expose_normalized_query() -> None:
    normalized_query = "PRIVATE-NORMALIZED-QUERY"
    request = parse_retrieval_request({"query": normalized_query})

    assert normalized_query not in repr(request)
    assert "normalized_query" not in repr(request)


def test_repeated_equivalent_parsing_is_deterministic() -> None:
    payload = {"query": "\u00a0e\u0301\tvalue\u3000", "requested_count": 7}

    assert parse_retrieval_request(payload) == parse_retrieval_request(payload)


def test_input_mapping_is_not_mutated() -> None:
    payload: dict[object, object] = {
        "query": "\u00a0alpha\t beta\u3000",
        "requested_count": 4,
    }
    before = payload.copy()

    parse_retrieval_request(payload)

    assert payload == before
