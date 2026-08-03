"""Static SQL contract tests for the AF-3A-03 PostgreSQL adapter."""

import pytest
from sqlalchemy.dialects import postgresql
from tests.retrieval_security import (
    CanonicalAcceptanceTuple,
    acceptance_tuple,
    arm_r24_log_capture,
    assert_r24_sidecar,
)

from app.db.models import KnowledgeBaseRole
from app.retrieval.postgres import (
    MAX_KEYWORD_CANDIDATES,
    _initial_authentication_statement,
    _initial_target_statement,
    _scoped_keyword_statement,
)
from app.security.authorization import Capability, capabilities_for

_KEYWORD_ORDER_UNIT = acceptance_tuple(
    "RET-KEY-001",
    "AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF",
    "unit",
)


def _compiled_sql(statement: object) -> str:
    compiled = statement.compile(dialect=postgresql.dialect())  # type: ignore[attr-defined]
    return " ".join(str(compiled).split())


def test_initial_access_sql_has_ordered_proof_and_exact_target_boundaries() -> None:
    authentication_sql = _compiled_sql(_initial_authentication_statement())
    target_sql = _compiled_sql(_initial_target_statement())

    assert "FROM user_sessions JOIN users" in authentication_sql
    assert "user_sessions.id = %(session_id)s" in authentication_sql
    assert "user_sessions.user_id = %(user_id)s" in authentication_sql
    assert "user_sessions.token_sha256 = %(session_token_sha256)s" in authentication_sql
    assert "user_sessions.revoked_at IS NULL" in authentication_sql
    assert "user_sessions.expires_at > %(now)s" in authentication_sql
    assert "users.is_active IS true" in authentication_sql

    assert "FROM knowledge_bases JOIN knowledge_base_memberships" in target_sql
    assert "knowledge_bases.id = %(knowledge_base_id)s" in target_sql
    assert "knowledge_base_memberships.user_id = %(user_id)s" in target_sql
    assert "knowledge_base_memberships.role IN" in target_sql


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_KEYWORD_ORDER_UNIT, id=_KEYWORD_ORDER_UNIT.pytest_id)],
)
def test_keyword_sql_scopes_before_score_ranks_then_limits(
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    compiled = _scoped_keyword_statement().compile(dialect=postgresql.dialect())
    sql = " ".join(str(compiled).split())
    parameters = compiled.params
    normalized_query_sentinel = "AF3A03-UNIT-QUERY-6f037671ec8344ccb7c236ca71ea99af"

    assert "WITH eligible_keyword_candidates AS" in sql
    assert "plainto_tsquery('simple'::regconfig, %(normalized_query)s)" in sql
    assert "to_tsvector('simple'::regconfig, document_chunks.normalized_text)" in sql
    assert "@@ plainto_tsquery" in sql
    assert "ts_rank_cd" in sql
    assert "knowledge_bases.id = %(knowledge_base_id)s" in sql
    assert "knowledge_base_memberships.user_id = %(user_id)s" in sql
    assert "user_sessions.token_sha256 = %(session_token_sha256)s" in sql
    assert "documents.status = %(status_1)s" in sql
    assert "document_chunks.content_sha256 IS NOT NULL" in sql
    assert "document_chunks.content_sha256 ~ %(content_sha256_1)s" in sql
    assert "row_number() OVER (ORDER BY eligible_keyword_candidates.keyword_score DESC" in sql
    assert "eligible_keyword_candidates.chunk_id ASC)" in sql
    assert "ORDER BY ranked_keyword_candidates.keyword_rank ASC" in sql
    assert "LIMIT %(param_1)s" in sql
    assert "count(" not in sql.lower()
    assert type(parameters["ts_rank_cd_1"]) is int
    assert parameters["ts_rank_cd_1"] == 0
    assert parameters["content_sha256_1"] == r"^[0-9a-f]{64}$"
    assert MAX_KEYWORD_CANDIDATES == 128
    assert normalized_query_sentinel not in sql
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(normalized_query_sentinel,),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": sql,
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


def test_current_role_matrix_grants_both_retrieval_reads_without_synthetic_role() -> None:
    assert tuple(KnowledgeBaseRole) == (
        KnowledgeBaseRole.OWNER,
        KnowledgeBaseRole.EDITOR,
        KnowledgeBaseRole.VIEWER,
    )
    for role in KnowledgeBaseRole:
        capabilities = capabilities_for(role)
        assert Capability.KNOWLEDGE_BASE_READ in capabilities
        assert Capability.DOCUMENT_READ in capabilities
