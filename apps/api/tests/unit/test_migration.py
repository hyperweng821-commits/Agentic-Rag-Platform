"""Offline upgrade/downgrade tests for the first AF-1 Alembic migration."""

from io import StringIO

from alembic import command
from alembic.config import Config


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
