"""Shared deterministic fixtures for AF-3B canonical executable evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from logging import LogRecord

from tests.retrieval_security import (
    AF3B_CANONICAL_TUPLES,
    CanonicalAcceptanceTuple,
    assert_r24_sidecar,
)

AF3B_LEVELS = (
    "unit",
    "provider-adapter contract",
    "PostgreSQL integration",
    "deterministic concurrency",
    "fault injection",
)
AF3B_EXPECTED_LEVEL_COUNTS = {
    "unit": 171,
    "provider-adapter contract": 167,
    "PostgreSQL integration": 218,
    "deterministic concurrency": 7,
    "fault injection": 17,
}
AF3B_R24_SENTINELS = (
    "af3b-raw-session-token-forbidden",
    "f4ad9feaa60e3318f03640c4716e3e6af79554f864d4d04bf03517ad37aa1b59",
    "af3b-provider-secret-forbidden",
    "af3b-provider-payload-detail-forbidden",
    "chunk:ffffffff-ffff-4fff-8fff-ffffffffffff",
    "af3b-unsafe-untrusted-content-forbidden",
)


def af3b_rows(test_level: str) -> tuple[CanonicalAcceptanceTuple, ...]:
    """Return one deterministic complete level projection for parametrization."""
    if test_level not in AF3B_LEVELS:
        raise AssertionError(f"Unknown AF-3B test level: {test_level!r}")
    rows = tuple(
        sorted(
            (row for row in AF3B_CANONICAL_TUPLES if row.test_level == test_level),
            key=lambda row: (
                row.case_id,
                row.variant,
                row.boundary,
                row.oracle,
            ),
        )
    )
    if len(rows) != AF3B_EXPECTED_LEVEL_COUNTS[test_level]:
        raise AssertionError(f"AF-3B {test_level} executable inventory changed")
    return rows


def af3b_pytest_param_id(row: CanonicalAcceptanceTuple) -> str:
    """Expose the complete canonical identity in every pytest node ID."""
    return row.pytest_id


def assert_af3b_r24(
    canonical_tuple: CanonicalAcceptanceTuple,
    *,
    sentinels: Sequence[str | bytes],
    log_records: Sequence[LogRecord],
    sinks: Mapping[str, object],
) -> None:
    """Invoke the shared R24 scanner for one exact AF-3B tuple."""
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=sentinels,
        log_records=log_records,
        sinks=sinks,
    )
