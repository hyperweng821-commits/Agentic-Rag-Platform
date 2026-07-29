"""Knowledge, ingestion, and access model metadata tests."""

from sqlalchemy import CheckConstraint

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)


def _constraint_names(table: object) -> set[str | None]:
    return {constraint.name for constraint in table.constraints}  # type: ignore[attr-defined]


def _check_sql(table: object) -> str:
    constraints = (
        constraint
        for constraint in table.constraints  # type: ignore[attr-defined]
        if isinstance(constraint, CheckConstraint)
    )
    return " ".join(str(constraint.sqltext) for constraint in constraints)


def test_knowledge_base_constraints_and_ordering_index_exist() -> None:
    assert {"ck_knowledge_bases_name_length", "ck_knowledge_bases_description_length"} <= (
        _constraint_names(KnowledgeBase.__table__)
    )
    assert "ix_knowledge_bases_created_at_id" in {
        index.name for index in KnowledgeBase.__table__.indexes
    }


def test_document_has_concurrent_deduplication_and_state_constraints() -> None:
    names = _constraint_names(Document.__table__)

    assert "uq_documents_knowledge_base_id_sha256" in names
    assert "uq_documents_storage_key" in names
    assert "ck_documents_positive_size" in names
    assert "ck_documents_sha256_length" in names
    assert "ck_documents_valid_status" in names
    assert set(DocumentStatus) == {
        DocumentStatus.PENDING,
        DocumentStatus.PROCESSING,
        DocumentStatus.COMPLETED,
        DocumentStatus.FAILED,
    }


def test_ingestion_job_enforces_one_job_per_document_and_explicit_states() -> None:
    names = _constraint_names(IngestionJob.__table__)

    assert "uq_ingestion_jobs_document_id" in names
    assert "ck_ingestion_jobs_nonnegative_attempt_count" in names
    assert "ck_ingestion_jobs_valid_status" in names
    assert set(IngestionJobStatus) == {
        IngestionJobStatus.PENDING,
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.FAILED,
    }


def test_ingestion_job_has_bounded_retry_progress_and_lease_metadata() -> None:
    columns = IngestionJob.__table__.c
    check_sql = _check_sql(IngestionJob.__table__)

    assert columns.max_attempts.default.arg == 3
    assert str(columns.max_attempts.server_default.arg) == "3"
    assert columns.progress_percent.default.arg == 0
    assert str(columns.progress_percent.server_default.arg) == "0"
    assert columns.claimed_by.nullable
    assert columns.claimed_at.nullable
    assert columns.lease_expires_at.nullable
    assert columns.next_retry_at.nullable
    assert "max_attempts > 0" in check_sql
    assert "attempt_count <= max_attempts" in check_sql
    assert "progress_percent BETWEEN 0 AND 100" in check_sql
    assert "btrim(claimed_by)" in check_sql
    assert "claimed_at" in check_sql
    assert "lease_expires_at" in check_sql


def test_ingestion_job_has_claimability_and_expired_lease_indexes() -> None:
    index_columns = {
        index.name: tuple(column.name for column in index.columns)
        for index in IngestionJob.__table__.indexes
    }

    assert index_columns["ix_ingestion_jobs_status_next_retry_at"] == (
        "status",
        "next_retry_at",
    )
    assert index_columns["ix_ingestion_jobs_status_lease_expires_at"] == (
        "status",
        "lease_expires_at",
    )


def test_document_chunk_has_deterministic_ordering_and_content_constraints() -> None:
    names = _constraint_names(DocumentChunk.__table__)
    check_sql = _check_sql(DocumentChunk.__table__)

    assert "uq_document_chunks_document_id_chunk_index" in names
    assert "chunk_index >= 0" in check_sql
    assert "token_count >= 0" in check_sql
    assert "btrim(normalized_text)" in check_sql
    assert DocumentChunk.__table__.c.normalized_text.nullable is False
    assert DocumentChunk.__table__.c.token_count.nullable is False


def test_document_chunk_has_nullable_validated_provenance_metadata() -> None:
    columns = DocumentChunk.__table__.c
    names = _constraint_names(DocumentChunk.__table__)
    check_sql = _check_sql(DocumentChunk.__table__)

    assert {
        "ck_document_chunks_valid_content_sha256",
        "ck_document_chunks_valid_source_offsets",
        "ck_document_chunks_valid_page_range",
    } <= names
    assert columns.content_sha256.nullable
    assert columns.start_offset.nullable
    assert columns.end_offset.nullable
    assert columns.page_start.nullable
    assert columns.page_end.nullable
    assert "^[0-9a-f]{64}$" in check_sql
    assert "start_offset >= 0" in check_sql
    assert "end_offset > start_offset" in check_sql
    assert "page_start > 0" in check_sql
    assert "page_end >= page_start" in check_sql


def test_document_to_chunk_relationship_uses_database_cascade() -> None:
    relationship = Document.chunks.property
    foreign_key = next(iter(DocumentChunk.__table__.c.document_id.foreign_keys))

    assert relationship.back_populates == "document"
    assert relationship.passive_deletes is True
    assert relationship.cascade.delete_orphan
    assert foreign_key.ondelete == "CASCADE"


def test_user_requires_normalized_email_and_argon2id_hash() -> None:
    columns = User.__table__.c
    names = _constraint_names(User.__table__)
    check_sql = _check_sql(User.__table__)

    assert columns.email.type.length == 320
    assert columns.email.nullable is False
    assert columns.password_hash.nullable is False
    assert columns.is_active.default.arg is True
    assert str(columns.is_active.server_default.arg) == "true"
    assert "uq_users_email" in names
    assert "ck_users_normalized_email" in names
    assert "ck_users_valid_password_hash" in names
    assert "email = lower(email)" in check_sql
    assert "email = btrim(email)" in check_sql
    assert "$argon2id$" in check_sql


def test_user_session_persists_only_valid_token_digests_and_lifecycle_times() -> None:
    columns = UserSession.__table__.c
    names = _constraint_names(UserSession.__table__)
    check_sql = _check_sql(UserSession.__table__)
    index_columns = {
        index.name: tuple(column.name for column in index.columns)
        for index in UserSession.__table__.indexes
    }

    assert columns.token_sha256.type.length == 64
    assert columns.csrf_token_sha256.type.length == 64
    assert columns.expires_at.type.timezone is True
    assert columns.revoked_at.type.timezone is True
    assert columns.last_seen_at.type.timezone is True
    assert "token" not in columns
    assert "csrf_token" not in columns
    assert "uq_user_sessions_token_sha256" in names
    assert "ck_user_sessions_valid_token_sha256" in names
    assert "ck_user_sessions_valid_csrf_token_sha256" in names
    assert check_sql.count("^[0-9a-f]{64}$") == 2
    assert index_columns["ix_user_sessions_user_id"] == ("user_id",)
    assert index_columns["ix_user_sessions_expires_at"] == ("expires_at",)
    assert index_columns["ix_user_sessions_active_user_expires_at"] == (
        "user_id",
        "revoked_at",
        "expires_at",
    )


def test_session_and_membership_foreign_keys_cascade() -> None:
    session_user_fk = next(iter(UserSession.__table__.c.user_id.foreign_keys))
    membership_kb_fk = next(
        iter(KnowledgeBaseMembership.__table__.c.knowledge_base_id.foreign_keys)
    )
    membership_user_fk = next(iter(KnowledgeBaseMembership.__table__.c.user_id.foreign_keys))

    assert session_user_fk.ondelete == "CASCADE"
    assert membership_kb_fk.ondelete == "CASCADE"
    assert membership_user_fk.ondelete == "CASCADE"
    assert User.sessions.property.passive_deletes is True
    assert User.knowledge_base_memberships.property.passive_deletes is True
    assert KnowledgeBase.memberships.property.passive_deletes is True


def test_membership_has_bounded_roles_and_bidirectional_lookup_indexes() -> None:
    names = _constraint_names(KnowledgeBaseMembership.__table__)
    check_sql = _check_sql(KnowledgeBaseMembership.__table__)
    index_columns = {
        index.name: tuple(column.name for column in index.columns)
        for index in KnowledgeBaseMembership.__table__.indexes
    }

    assert set(KnowledgeBaseRole) == {
        KnowledgeBaseRole.OWNER,
        KnowledgeBaseRole.EDITOR,
        KnowledgeBaseRole.VIEWER,
    }
    assert {
        "knowledge_base_id",
        "user_id",
    } == {column.name for column in KnowledgeBaseMembership.__table__.primary_key.columns}
    assert "uq_knowledge_base_memberships_knowledge_base_id_user_id" in names
    assert "ck_knowledge_base_memberships_valid_role" in names
    assert "owner" in check_sql
    assert "editor" in check_sql
    assert "viewer" in check_sql
    assert index_columns["ix_knowledge_base_memberships_user_id_knowledge_base_id"] == (
        "user_id",
        "knowledge_base_id",
    )
