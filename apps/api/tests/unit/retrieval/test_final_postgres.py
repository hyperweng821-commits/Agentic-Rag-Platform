"""Static PostgreSQL contracts for the AF-3A-04 final boundary."""

import hashlib
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from tests.retrieval_security import (
    CanonicalAcceptanceTuple,
    af3a04_acceptance_tuple,
    arm_r24_log_capture,
    assert_r24_sidecar,
)

from app.retrieval.postgres import (
    PostgresFinalAuthoritativeLoader,
    _final_authorization_parameters,
    _final_authorization_statement,
    _final_candidate_statement,
)
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal


def _unit(variant: str) -> CanonicalAcceptanceTuple:
    return af3a04_acceptance_tuple("RET-CONC-013", variant, "unit")


_EXPIRY_ROWS = (
    _unit("EXPIRES-EQUALITY-EXPIRED"),
    _unit("EXPIRES-GREATER-VALID"),
)
_FRESH_ROW = _unit("FINAL-NOW-FRESH-AWARE")


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(row, id=row.pytest_id) for row in _EXPIRY_ROWS],
)
def test_final_authorization_uses_strict_expiry_and_same_statement_snapshot_proof(
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    compiled = _final_authorization_statement().compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    user_id = uuid4()
    session_id = uuid4()
    knowledge_base_id = uuid4()
    token_digest = hashlib.sha256(f"unit-token:{uuid4()}".encode()).hexdigest()
    proof = SessionAuthenticationProof(
        principal=Principal(
            user_id=user_id,
            email=f"af3a04-clock-{uuid4()}@example.com",
            session_id=session_id,
        ),
        session_token_sha256=token_digest,
    )
    final_now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    parameters = _final_authorization_parameters(
        proof=proof,
        knowledge_base_id=knowledge_base_id,
        final_now=final_now,
    )

    assert "user_sessions.expires_at > %(final_now)s" in sql
    assert "user_sessions.expires_at >=" not in sql
    assert "user_sessions.id = %(session_id)s" in sql
    assert "user_sessions.user_id = %(user_id)s" in sql
    assert "user_sessions.token_sha256 = %(session_token_sha256)s" in sql
    assert "user_sessions.revoked_at IS NULL" in sql
    assert "users.is_active IS true" in sql
    assert "knowledge_bases.id = %(knowledge_base_id)s" in sql
    assert "knowledge_base_memberships.user_id = %(user_id)s" in sql
    assert "knowledge_base_memberships.role IN" in sql
    assert "current_setting('transaction_isolation')" in sql
    assert "current_setting('transaction_read_only')" in sql
    assert parameters == {
        "session_id": session_id,
        "user_id": user_id,
        "session_token_sha256": token_digest,
        "knowledge_base_id": knowledge_base_id,
        "final_now": final_now,
    }
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(str(user_id), str(session_id), token_digest, str(knowledge_base_id)),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": (sql,),
            "service_diagnostics": {
                "parameter_names": tuple(parameters),
                "parameter_types": tuple(type(value).__name__ for value in parameters.values()),
            },
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_FRESH_ROW, id=_FRESH_ROW.pytest_id)],
)
def test_final_clock_is_injected_once_and_requires_timezone_aware_utc(
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    final_now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    calls: list[str] = []
    clock_context = f"clock-context-{uuid4()}"

    def clock() -> datetime:
        calls.append(clock_context)
        return final_now

    loader = PostgresFinalAuthoritativeLoader(None, clock=clock)  # type: ignore[arg-type]
    assert loader._final_now() is final_now
    assert calls == [clock_context]

    captured_errors: list[RuntimeError] = []
    for invalid in (
        datetime(2026, 8, 4, 12, 0),
        datetime(2026, 8, 4, 12, 0, tzinfo=timezone(timedelta(hours=1))),
    ):
        invalid_loader = PostgresFinalAuthoritativeLoader(  # type: ignore[arg-type]
            None,
            clock=lambda invalid=invalid: invalid,
        )
        with pytest.raises(RuntimeError, match="aware UTC") as captured:
            invalid_loader._final_now()
        captured_errors.append(captured.value)

    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(clock_context,),
        log_records=caplog.records,
        sinks={
            "exception_error_records": tuple(captured_errors),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": (),
            "service_diagnostics": {
                "clock_call_count": len(calls),
                "invalid_clock_count": len(captured_errors),
                "returned_timezone": str(final_now.tzinfo),
            },
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


def test_candidate_projection_is_exact_target_completed_and_persisted_hash_only() -> None:
    compiled = _final_candidate_statement().compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())

    assert "knowledge_bases.id = %(knowledge_base_id)s" in sql
    assert "document_chunks.id IN (__[POSTCOMPILE_candidate_ids])" in sql
    assert "documents.status = %(status_1)s" in sql
    assert "document_chunks.content_sha256 IS NOT NULL" in sql
    assert "document_chunks.content_sha256 ~ %(content_sha256_1)s" in sql
    assert compiled.params["status_1"] == "completed"
    assert compiled.params["content_sha256_1"] == r"^[0-9a-f]{64}$"
    for field in (
        "knowledge_base_id",
        "document_id",
        "chunk_id",
        "normalized_text",
        "content_sha256",
        "source_display_name",
        "page_start",
        "page_end",
        "character_start",
        "character_end",
    ):
        assert field in sql
    assert "storage_key" not in sql
