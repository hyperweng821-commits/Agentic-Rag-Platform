"""Offline upgrade/downgrade tests for the AF-1 and AF-2A migrations."""

from io import StringIO

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


def _config(output: StringIO) -> Config:
    config = Config("alembic.ini", stdout=output, output_buffer=output)
    config.set_main_option(
        "sqlalchemy.url",
        "postgresql+asyncpg://test:test@localhost/test",
    )
    return config


def test_migration_upgrade_generates_all_af1_tables() -> None:
    output = StringIO()

    command.upgrade(_config(output), "head", sql=True)

    sql = output.getvalue()
    assert "CREATE TABLE knowledge_bases" in sql
    assert "CREATE TABLE documents" in sql
    assert "CREATE TABLE ingestion_jobs" in sql
    assert "uq_documents_knowledge_base_id_sha256" in sql
    assert "uq_ingestion_jobs_document_id" in sql


def test_migration_downgrade_removes_all_af1_tables_in_reverse_order() -> None:
    output = StringIO()

    command.downgrade(_config(output), "20260727_0001:base", sql=True)

    sql = output.getvalue()
    assert sql.index("DROP TABLE ingestion_jobs") < sql.index("DROP TABLE documents")
    assert sql.index("DROP TABLE documents") < sql.index("DROP TABLE knowledge_bases")


def test_af2a_migration_is_the_single_current_head() -> None:
    scripts = ScriptDirectory.from_config(_config(StringIO()))

    assert scripts.get_current_head() == "20260728_0002"
    assert scripts.get_revision("20260728_0002").down_revision == "20260727_0001"


def test_af2a_upgrade_adds_job_leases_and_document_chunks() -> None:
    output = StringIO()

    command.upgrade(_config(output), "20260727_0001:head", sql=True)

    sql = output.getvalue()
    assert "ALTER TABLE ingestion_jobs ADD COLUMN max_attempts" in sql
    assert "ALTER TABLE ingestion_jobs ADD COLUMN progress_percent" in sql
    assert "ALTER TABLE ingestion_jobs ADD COLUMN claimed_by" in sql
    assert "ALTER TABLE ingestion_jobs ADD COLUMN claimed_at" in sql
    assert "ALTER TABLE ingestion_jobs ADD COLUMN lease_expires_at" in sql
    assert "ALTER TABLE ingestion_jobs ADD COLUMN next_retry_at" in sql
    assert "ck_ingestion_jobs_positive_max_attempts" in sql
    assert "ck_ingestion_jobs_attempt_count_within_max_attempts" in sql
    assert "ck_ingestion_jobs_progress_percent_range" in sql
    assert "ck_ingestion_jobs_claimed_by_nonblank" in sql
    assert "ck_ingestion_jobs_lease_fields_consistent" in sql
    assert "ck_ingestion_jobs_lease_window" in sql
    assert "ix_ingestion_jobs_status_next_retry_at" in sql
    assert "ix_ingestion_jobs_status_lease_expires_at" in sql
    assert "CREATE TABLE document_chunks" in sql
    assert "uq_document_chunks_document_id_chunk_index" in sql
    assert "ck_document_chunks_nonnegative_chunk_index" in sql
    assert "ck_document_chunks_nonnegative_token_count" in sql
    assert "ck_document_chunks_nonempty_normalized_text" in sql
    assert "ON DELETE CASCADE" in sql


def test_af2a_downgrade_removes_only_af2a_schema() -> None:
    output = StringIO()

    command.downgrade(_config(output), "head:20260727_0001", sql=True)

    sql = output.getvalue()
    assert "DROP TABLE document_chunks" in sql
    assert "DROP INDEX ix_ingestion_jobs_status_lease_expires_at" in sql
    assert "DROP INDEX ix_ingestion_jobs_status_next_retry_at" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN next_retry_at" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN lease_expires_at" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN claimed_at" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN claimed_by" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN progress_percent" in sql
    assert "ALTER TABLE ingestion_jobs DROP COLUMN max_attempts" in sql
    assert "DROP TABLE ingestion_jobs" not in sql
    assert "DROP TABLE documents" not in sql
    assert "DROP TABLE knowledge_bases" not in sql
