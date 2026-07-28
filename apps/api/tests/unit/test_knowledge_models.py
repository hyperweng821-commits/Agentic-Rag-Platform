"""AF-1 and AF-2A model metadata and database-constraint tests."""

from sqlalchemy import CheckConstraint

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
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


def test_document_to_chunk_relationship_uses_database_cascade() -> None:
    relationship = Document.chunks.property
    foreign_key = next(iter(DocumentChunk.__table__.c.document_id.foreign_keys))

    assert relationship.back_populates == "document"
    assert relationship.passive_deletes is True
    assert relationship.cascade.delete_orphan
    assert foreign_key.ondelete == "CASCADE"
