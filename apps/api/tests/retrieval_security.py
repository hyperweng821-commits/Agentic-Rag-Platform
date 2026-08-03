"""Shared AF-3A acceptance identities and recursive R24 sink scanning."""

# ruff: noqa: E501 -- ledger rows remain byte-for-byte single-line identities.

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from logging import LogRecord
from typing import Protocol


class R24LogCapture(Protocol):
    """Minimal pytest log-capture surface required by the R24 sidecar."""

    records: list[LogRecord]

    def set_level(self, level: int, logger: str | None = None) -> None: ...


@dataclass(frozen=True, slots=True)
class CanonicalAcceptanceTuple:
    """One complete executable acceptance identity from the canonical ledger."""

    case_id: str
    variant: str
    test_level: str
    boundary: str
    owner: str
    status: str
    oracle: str

    @property
    def label(self) -> str:
        return f"{self.case_id}::{self.variant}"

    @property
    def pytest_id(self) -> str:
        level = self.test_level.replace(" ", "-")
        return f"{self.label}@{level}[{self.boundary}]"


_AF3A03_LEDGER_ROWS = """
RET-AUTH-002|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-AUTH-003|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-AUTH-004|AF3A-ROLE-MATRIX|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-ROLE-MATRIX
RET-AUTH-005|AF3A-NONMEMBER-INITIAL-ACCESS|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-NONMEMBER-INITIAL-ACCESS
RET-AUTH-006|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-AUTH-007|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-AUTH-008|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-AUTH-009|AF3A-KEYWORD-EXACT-TARGET|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-EXACT-TARGET
RET-AUTH-010|AF3A-INITIAL-ACCESS-ZERO-HIT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-INITIAL-ACCESS-ZERO-HIT
RET-AUTH-011|DEFAULT|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-DEFAULT
RET-BND-001|AF3A-EMBEDDED-U0000-GATE-ORDER|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-EMBEDDED-U0000-GATE-ORDER
RET-BND-001|AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER
RET-BND-001|AF3A-KEYWORD-BIND-CASE-SENSITIVE|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-BIND-CASE-SENSITIVE
RET-BND-001|AF3A-KEYWORD-BIND-EXCLUDED-U200B|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-BIND-EXCLUDED-U200B
RET-BND-001|AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE
RET-BND-001|AF3A-KEYWORD-BIND-NO-NFKC|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-BIND-NO-NFKC
RET-BND-001|AF3A-KEYWORD-BIND-POST-NORMALIZATION-BOUNDARY|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-BIND-POST-NORMALIZATION-BOUNDARY
RET-BND-001|AF3A-U0000-ALONE-GATE-ORDER|PostgreSQL integration|AF3A_INITIAL_ACCESS|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-U0000-ALONE-GATE-ORDER
RET-BND-003|AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD
RET-BND-003|AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT
RET-BND-006|AF3A-KEYWORD-LIMIT-EXACT-128|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-LIMIT-EXACT-128
RET-KEY-001|AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF|unit|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF
RET-KEY-001|AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF
RET-KEY-003|AF3A-NO-GLOBAL-RESULT-COUNT|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-NO-GLOBAL-RESULT-COUNT
RET-KEY-004|AF3A-SCOPED-REPOSITORY-ONLY|unit|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SCOPED-REPOSITORY-ONLY
RET-KEY-004|AF3A-SCOPED-REPOSITORY-ONLY|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SCOPED-REPOSITORY-ONLY
RET-PRIV-004|KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY|PostgreSQL integration|AF3A_KEYWORD|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY
""".strip()


def _parse_ledger() -> frozenset[CanonicalAcceptanceTuple]:
    rows: set[CanonicalAcceptanceTuple] = set()
    for row in _AF3A03_LEDGER_ROWS.splitlines():
        fields = row.split("|")
        if len(fields) != 7:
            raise AssertionError(f"Invalid AF-3A-03 ledger row: {row!r}")
        rows.add(CanonicalAcceptanceTuple(*fields))
    if len(rows) != 27:
        raise AssertionError("AF-3A-03 ledger projection must contain exactly 27 tuples")
    return frozenset(rows)


AF3A03_CANONICAL_TUPLES = _parse_ledger()

_AF3A_EXPLICIT_SINKS = frozenset(
    {
        "exception_error_records",
        "trace_span_names_attributes_status_events",
        "postgres_sql_database_driver_transaction_diagnostics",
        "service_diagnostics",
        "internal_authoritative_retrieval_record_diagnostics",
    }
)


def arm_r24_log_capture(log_capture: R24LogCapture) -> None:
    """Capture DEBUG and higher application logs before an R24 execution."""
    log_capture.set_level(logging.DEBUG)


def acceptance_tuple(
    case_id: str,
    variant: str,
    test_level: str,
) -> CanonicalAcceptanceTuple:
    """Resolve one exact AF-3A-03 identity, rejecting aliases or partial keys."""
    matches = [
        row
        for row in AF3A03_CANONICAL_TUPLES
        if (row.case_id, row.variant, row.test_level) == (case_id, variant, test_level)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one canonical AF-3A-03 tuple for {(case_id, variant, test_level)!r}"
        )
    return matches[0]


def assert_r24_sidecar(
    canonical_tuple: CanonicalAcceptanceTuple,
    *,
    sentinels: Iterable[str | bytes],
    log_records: Sequence[LogRecord],
    sinks: Mapping[str, object],
) -> None:
    """Scan every registered AF-3A sink for exact or substring sentinel leaks."""
    if canonical_tuple not in AF3A03_CANONICAL_TUPLES:
        raise AssertionError(f"Unknown canonical tuple: {canonical_tuple!r}")

    normalized_sentinels = _normalize_sentinels(sentinels)
    supplied_sinks = set(sinks)
    if supplied_sinks != _AF3A_EXPLICIT_SINKS:
        missing = sorted(_AF3A_EXPLICIT_SINKS - supplied_sinks)
        unexpected = sorted(supplied_sinks - _AF3A_EXPLICIT_SINKS)
        raise AssertionError(
            "AF-3A R24 rows must explicitly register every owned sink; "
            f"missing={missing!r}, unexpected={unexpected!r}"
        )

    captured_log_records = tuple(_render_log_record(record) for record in log_records)
    observable_sinks: dict[str, object] = {
        "application_logs": captured_log_records,
        "access_logs": (),
        "structured_log_records": captured_log_records,
    }
    observable_sinks.update(sinks)

    for sink_name, sink_value in observable_sinks.items():
        for rendered in _walk_rendered(sink_value, seen=set()):
            for sentinel_text, sentinel_bytes in normalized_sentinels:
                if isinstance(rendered, bytes):
                    leaked = sentinel_bytes in rendered
                else:
                    leaked = sentinel_text in rendered
                if leaked:
                    raise AssertionError(
                        f"{canonical_tuple.pytest_id} leaked a sentinel in {sink_name}"
                    )


def _normalize_sentinels(
    sentinels: Iterable[str | bytes],
) -> tuple[tuple[str, bytes], ...]:
    normalized: list[tuple[str, bytes]] = []
    for sentinel in sentinels:
        if isinstance(sentinel, bytes):
            sentinel_bytes = sentinel
            sentinel_text = sentinel.decode("utf-8", errors="strict")
        elif isinstance(sentinel, str):
            sentinel_text = sentinel
            sentinel_bytes = sentinel.encode("utf-8", errors="strict")
        else:
            raise AssertionError("R24 sentinels must be exact str or bytes values")
        if not sentinel_text:
            raise AssertionError("R24 sentinels must be nonempty")
        normalized.append((sentinel_text, sentinel_bytes))

    if not normalized:
        raise AssertionError("R24 rows must register at least one sentinel")
    if len(set(normalized)) != len(normalized):
        raise AssertionError("R24 sentinels must be pairwise distinct")
    for index, (left_text, _) in enumerate(normalized):
        for right_text, _ in normalized[index + 1 :]:
            if left_text in right_text or right_text in left_text:
                raise AssertionError("R24 sentinels must not contain one another")
    return tuple(normalized)


def _render_log_record(record: LogRecord) -> Mapping[str, object]:
    return {
        "record_fields": dict(vars(record)),
        "rendered_message": record.getMessage(),
    }


def _walk_rendered(value: object, *, seen: set[int]) -> Iterable[str | bytes]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, bytes):
        yield value
        return

    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)

    if isinstance(value, BaseException):
        yield str(value)
        yield repr(value)
        yield from _walk_rendered(value.args, seen=seen)
        yield from _walk_rendered(value.__cause__, seen=seen)
        yield from _walk_rendered(value.__context__, seen=seen)
        yield from _walk_rendered(getattr(value, "__notes__", ()), seen=seen)
        yield from _walk_rendered(vars(value), seen=seen)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_rendered(key, seen=seen)
            yield from _walk_rendered(item, seen=seen)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_rendered(item, seen=seen)
        return
    if isinstance(value, (set, frozenset)):
        for item in value:
            yield from _walk_rendered(item, seen=seen)
        return

    yield repr(value)
