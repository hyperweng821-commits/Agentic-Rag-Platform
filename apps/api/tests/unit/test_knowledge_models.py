"""AF-1 model metadata and database-constraint tests."""

from app.db.models import Document, DocumentStatus, IngestionJob, IngestionJobStatus, KnowledgeBase


def _constraint_names(table: object) -> set[str | None]:
    return {constraint.name for constraint in table.constraints}  # type: ignore[attr-defined]


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
