"""Shared AF-3A acceptance identities and recursive R24 sink scanning."""

# ruff: noqa: E501 -- ledger rows remain byte-for-byte single-line identities.

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from logging import LogRecord
from pathlib import Path
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


_PURE_REQUEST_VALIDATOR_REMEDIATION_LEDGER_ROWS = """
RET-BND-001|POST-NORMALIZATION-SCALAR-BOUNDARY|unit|PURE_REQUEST_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-POST-NORMALIZATION-SCALAR-BOUNDARY
RET-BND-003|PARSER-NEGATIVE-ONE-REJECTED|unit|PURE_REQUEST_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-PARSER-NEGATIVE-ONE-REJECTED
""".strip()


def _parse_pure_request_validator_remediation_ledger() -> frozenset[CanonicalAcceptanceTuple]:
    rows: list[CanonicalAcceptanceTuple] = []
    for row in _PURE_REQUEST_VALIDATOR_REMEDIATION_LEDGER_ROWS.splitlines():
        fields = row.split("|")
        if len(fields) != 7:
            raise AssertionError(f"Invalid pure-request remediation row: {row!r}")
        rows.append(CanonicalAcceptanceTuple(*fields))
    if len(rows) != 2 or len(set(rows)) != 2:
        raise AssertionError("Pure-request remediation must contain exactly two tuples")
    return frozenset(rows)


PURE_REQUEST_VALIDATOR_REMEDIATION_TUPLES = _parse_pure_request_validator_remediation_ledger()


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

_AF3A04_LEDGER_ROWS = """
RET-AUTH-010|AF3A-FINAL-REAUTH-ZERO-CANDIDATES|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-FINAL-REAUTH-ZERO-CANDIDATES
RET-AUTH-010|AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES
RET-BND-008|AF3A-ZERO-SYNTHETIC-CANDIDATES|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-ZERO-SYNTHETIC-CANDIDATES
RET-BND-008|AF3A-ZERO-SYNTHETIC-CANDIDATES|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-ZERO-SYNTHETIC-CANDIDATES
RET-BND-009|AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE
RET-BND-009|AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE
RET-BND-010|AF3A-SYNTHETIC-EXACT-BATCH-64|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SYNTHETIC-EXACT-BATCH-64
RET-BND-010|AF3A-SYNTHETIC-EXACT-BATCH-64|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-EXACT-BATCH-64
RET-BND-011|AF3A-SYNTHETIC-BATCH-PLUS-ONE-65|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SYNTHETIC-BATCH-PLUS-ONE-65
RET-BND-011|AF3A-SYNTHETIC-BATCH-PLUS-ONE-65|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-BATCH-PLUS-ONE-65
RET-BND-012|AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES
RET-BND-012|AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES
RET-BND-013|AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT
RET-BND-013|AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT
RET-BND-014|AF3A-SYNTHETIC-UNORDERED-POSTGRESQL-ROWS|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-UNORDERED-POSTGRESQL-ROWS
RET-BND-015|AF3A-SYNTHETIC-MAXIMUM-192-THREE-BATCHES|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-MAXIMUM-192-THREE-BATCHES
RET-CONC-013|EXPIRES-EQUALITY-EXPIRED|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-EXPIRES-EQUALITY-EXPIRED
RET-CONC-013|EXPIRES-EQUALITY-EXPIRED|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-EXPIRES-EQUALITY-EXPIRED
RET-CONC-013|EXPIRES-GREATER-VALID|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-EXPIRES-GREATER-VALID
RET-CONC-013|EXPIRES-GREATER-VALID|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-EXPIRES-GREATER-VALID
RET-CONC-013|FINAL-NOW-FRESH-AWARE|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-FINAL-NOW-FRESH-AWARE
RET-CONC-013|FINAL-NOW-FRESH-AWARE|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-FINAL-NOW-FRESH-AWARE
RET-EVID-001|AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION
RET-EVID-001|AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION
RET-EVID-002|AF3A-NULL-HASH-OMISSION|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-NULL-HASH-OMISSION
RET-EVID-010|AF3A-ALL-INELIGIBLE-AUTHORIZED-EMPTY|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-ALL-INELIGIBLE-AUTHORIZED-EMPTY
RET-INJ-001|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-001|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-002|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-002|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-003|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-003|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-004|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-004|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-005|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-005|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-006|AF3A-KEYWORD-INTERNAL-RECORD|unit|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-U-AF3A-KEYWORD-INTERNAL-RECORD
RET-INJ-006|AF3A-KEYWORD-INTERNAL-RECORD|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-INTERNAL-RECORD
RET-KEY-002|AF3A-CROSS-SCOPE-REVALIDATION|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-CROSS-SCOPE-REVALIDATION
""".strip()


def _parse_af3a04_ledger() -> frozenset[CanonicalAcceptanceTuple]:
    rows: list[CanonicalAcceptanceTuple] = []
    for row in _AF3A04_LEDGER_ROWS.splitlines():
        fields = row.split("|")
        if len(fields) != 7:
            raise AssertionError(f"Invalid AF-3A-04 ledger row: {row!r}")
        rows.append(CanonicalAcceptanceTuple(*fields))
    if len(rows) != 39 or len(set(rows)) != 39:
        raise AssertionError("AF-3A-04 ledger projection must contain exactly 39 tuples")
    return frozenset(rows)


AF3A04_CANONICAL_TUPLES = _parse_af3a04_ledger()

_AF3A05_LEDGER_ROWS = """
RET-CONC-002|AF3A-KEYWORD-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT
RET-CONC-003|AF3A-KEYWORD-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT
RET-CONC-004|AF3A-KEYWORD-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT
RET-CONC-004|AF3A-KEYWORD-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT
RET-CONC-005|AF3A-KEYWORD-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT
RET-CONC-006|AF3A-SYNTHETIC-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT
RET-CONC-007|AF3A-KEYWORD-DOCUMENT-CHANGED-AFTER-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-DOCUMENT-CHANGED-AFTER-SNAPSHOT
RET-CONC-008|AF3A-KEYWORD-CHUNK-REPLACED-AFTER-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-CHUNK-REPLACED-AFTER-SNAPSHOT
RET-CONC-009|AF3A-KEYWORD-REVOCATION-AFTER-FINAL-COMMIT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-KEYWORD-REVOCATION-AFTER-FINAL-COMMIT
RET-CONC-010|AF3A-SYNTHETIC-MULTIBATCH-FIXED-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-SYNTHETIC-MULTIBATCH-FIXED-SNAPSHOT
RET-CONC-011|AF3A-BATCH-TWO-STATEMENT-FAILURE|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-BATCH-TWO-STATEMENT-FAILURE
RET-CONC-011|AF3A-BATCH-TWO-STATEMENT-TIMEOUT|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-BATCH-TWO-STATEMENT-TIMEOUT
RET-CONC-011|AF3A-FINAL-COMMIT-FAILURE|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-FINAL-COMMIT-FAILURE
RET-CONC-011|AF3A-FINAL-CONNECTION-FAILURE|PostgreSQL integration|AF3A_FINAL_VALIDATOR|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-FINAL-CONNECTION-FAILURE
RET-CONC-012|AF3A-ZERO-CANDIDATE-ACCESS-LOSS|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-ZERO-CANDIDATE-ACCESS-LOSS
RET-CONC-013|AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY
RET-CONC-013|AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY|deterministic concurrency|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-DC-AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY
RET-CONC-014|AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT|PostgreSQL integration|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-PG-AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT
RET-CONC-014|AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT|deterministic concurrency|AF3A_CONCURRENCY|AF-3A|REQUIRED_NOT_YET_IMPLEMENTED|O-DC-AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT
""".strip()


def _parse_af3a05_ledger() -> frozenset[CanonicalAcceptanceTuple]:
    rows: list[CanonicalAcceptanceTuple] = []
    for row in _AF3A05_LEDGER_ROWS.splitlines():
        fields = row.split("|")
        if len(fields) != 7:
            raise AssertionError(f"Invalid AF-3A-05 ledger row: {row!r}")
        rows.append(CanonicalAcceptanceTuple(*fields))
    if len(rows) != 19 or len(set(rows)) != 19:
        raise AssertionError("AF-3A-05 ledger projection must contain exactly 19 tuples")
    return frozenset(rows)


AF3A05_CANONICAL_TUPLES = _parse_af3a05_ledger()

_AF3B_LEDGER_PROJECTION_SHA256 = (
    "8166a00d64b483090ce6dee5fa82a74adfc2dd28873abd0434a8d60c0045f59a"
)
_AF3B_LEVEL_COUNTS = {
    "unit": 171,
    "provider-adapter contract": 167,
    "PostgreSQL integration": 218,
    "deterministic concurrency": 7,
    "fault injection": 17,
}


def _parse_af3b_ledger() -> frozenset[CanonicalAcceptanceTuple]:
    """Load the hash-pinned AF-3B projection from the committed canonical ledger."""
    repository_root = Path(__file__).resolve().parents[3]
    ledger_path = repository_root / "docs" / "retrieval-security-acceptance.md"
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    inside = False
    projected_lines: list[str] = []
    rows: list[CanonicalAcceptanceTuple] = []
    for line in lines:
        if line == "<!-- CANONICAL_LEDGER_BEGIN -->":
            inside = True
            continue
        if line == "<!-- CANONICAL_LEDGER_END -->":
            inside = False
            break
        if not inside or not line.startswith("|"):
            continue
        fields = tuple(field.strip() for field in line.strip("|").split("|"))
        if len(fields) != 7 or fields[4] != "AF-3B":
            continue
        projected_lines.append(line)
        rows.append(CanonicalAcceptanceTuple(*fields))

    projection = "".join(f"{line}\n" for line in projected_lines).encode()
    if hashlib.sha256(projection).hexdigest() != _AF3B_LEDGER_PROJECTION_SHA256:
        raise AssertionError("AF-3B canonical ledger projection hash changed")
    if len(rows) != 580 or len(set(rows)) != 580:
        raise AssertionError("AF-3B ledger projection must contain 580 unique tuples")
    for level, expected_count in _AF3B_LEVEL_COUNTS.items():
        if sum(row.test_level == level for row in rows) != expected_count:
            raise AssertionError(f"AF-3B {level} inventory changed")
    if any(row.status != "REQUIRED_NOT_YET_IMPLEMENTED" for row in rows):
        raise AssertionError("AF-3B ledger status changed during implementation")
    return frozenset(rows)


AF3B_CANONICAL_TUPLES = _parse_af3b_ledger()

_AF3A_EXPLICIT_SINKS = frozenset(
    {
        "exception_error_records",
        "trace_span_names_attributes_status_events",
        "postgres_sql_database_driver_transaction_diagnostics",
        "service_diagnostics",
        "internal_authoritative_retrieval_record_diagnostics",
    }
)
_AF3B_EXPLICIT_SINKS = _AF3A_EXPLICIT_SINKS | frozenset(
    {
        "embedding_provider_request_response_diagnostics",
        "chroma_provider_request_response_diagnostics",
        "hybrid_result_diagnostics",
    }
)


def arm_r24_log_capture(log_capture: R24LogCapture) -> None:
    """Capture DEBUG and higher application logs before an R24 execution."""
    log_capture.set_level(logging.DEBUG)


def pure_request_validator_remediation_tuple(
    case_id: str,
    variant: str,
    test_level: str,
) -> CanonicalAcceptanceTuple:
    """Resolve one exact pure-request closure-remediation identity."""
    matches = [
        row
        for row in PURE_REQUEST_VALIDATOR_REMEDIATION_TUPLES
        if (row.case_id, row.variant, row.test_level) == (case_id, variant, test_level)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one pure-request remediation tuple for {(case_id, variant, test_level)!r}"
        )
    return matches[0]


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


def af3a04_acceptance_tuple(
    case_id: str,
    variant: str,
    test_level: str,
) -> CanonicalAcceptanceTuple:
    """Resolve one exact AF-3A-04 identity without altering AF-3A-03 keys."""
    matches = [
        row
        for row in AF3A04_CANONICAL_TUPLES
        if (row.case_id, row.variant, row.test_level) == (case_id, variant, test_level)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one canonical AF-3A-04 tuple for {(case_id, variant, test_level)!r}"
        )
    return matches[0]


def af3a05_acceptance_tuple(
    case_id: str,
    variant: str,
    test_level: str,
) -> CanonicalAcceptanceTuple:
    """Resolve one exact AF-3A-05 concurrency identity."""
    matches = [
        row
        for row in AF3A05_CANONICAL_TUPLES
        if (row.case_id, row.variant, row.test_level) == (case_id, variant, test_level)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one canonical AF-3A-05 tuple for {(case_id, variant, test_level)!r}"
        )
    return matches[0]


def af3b_acceptance_tuple(
    case_id: str,
    variant: str,
    test_level: str,
) -> CanonicalAcceptanceTuple:
    """Resolve one exact hash-pinned AF-3B executable identity."""
    matches = [
        row
        for row in AF3B_CANONICAL_TUPLES
        if (row.case_id, row.variant, row.test_level) == (case_id, variant, test_level)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one canonical AF-3B tuple for {(case_id, variant, test_level)!r}"
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
    if canonical_tuple not in (
        PURE_REQUEST_VALIDATOR_REMEDIATION_TUPLES
        | AF3A03_CANONICAL_TUPLES
        | AF3A04_CANONICAL_TUPLES
        | AF3A05_CANONICAL_TUPLES
        | AF3B_CANONICAL_TUPLES
    ):
        raise AssertionError(f"Unknown canonical tuple: {canonical_tuple!r}")

    normalized_sentinels = _normalize_sentinels(sentinels)
    expected_sinks = (
        _AF3B_EXPLICIT_SINKS if canonical_tuple.owner == "AF-3B" else _AF3A_EXPLICIT_SINKS
    )
    supplied_sinks = set(sinks)
    if supplied_sinks != expected_sinks:
        missing = sorted(expected_sinks - supplied_sinks)
        unexpected = sorted(supplied_sinks - expected_sinks)
        raise AssertionError(
            "R24 rows must explicitly register every owned sink; "
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
    if is_dataclass(value) and not isinstance(value, type):
        for data_field in fields(value):
            yield data_field.name
            yield from _walk_rendered(getattr(value, data_field.name), seen=seen)
        return

    state = getattr(value, "__dict__", None)
    if isinstance(state, Mapping):
        yield from _walk_rendered(state, seen=seen)

    slot_names: list[str] = []
    for owner in type(value).__mro__:
        declared = getattr(owner, "__slots__", ())
        if isinstance(declared, str):
            declared = (declared,)
        slot_names.extend(
            name for name in declared if name not in {"__dict__", "__weakref__"}
        )
    for slot_name in dict.fromkeys(slot_names):
        try:
            slot_value = getattr(value, slot_name)
        except AttributeError:
            continue
        yield slot_name
        yield from _walk_rendered(slot_value, seen=seen)
