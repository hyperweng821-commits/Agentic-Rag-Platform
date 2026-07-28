"""Focused tests for AF-1 and AF-2A repository query and flush behavior."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
)
from app.db.repositories import (
    DocumentChunkRepository,
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseRepository,
)


def _postgresql_sql(statement: object) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))  # type: ignore[attr-defined]


async def test_repository_adds_flush_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    knowledge_base = KnowledgeBase(name="Engineering")

    await KnowledgeBaseRepository(session).add(knowledge_base)

    session.add.assert_called_once_with(knowledge_base)
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


async def test_knowledge_base_list_uses_bounded_deterministic_query() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result

    result = await KnowledgeBaseRepository(session).list(limit=20, offset=10)

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = str(statement)
    assert "ORDER BY knowledge_bases.created_at ASC, knowledge_bases.id ASC" in rendered
    assert statement._limit_clause.value == 20
    assert statement._offset_clause.value == 10


async def test_document_digest_query_scopes_to_knowledge_base() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    knowledge_base_id = uuid4()

    result = await DocumentRepository(session).get_by_digest(
        knowledge_base_id=knowledge_base_id,
        sha256="a" * 64,
    )

    assert result is None
    rendered = str(session.scalar.await_args.args[0])
    assert "documents.knowledge_base_id" in rendered
    assert "documents.sha256" in rendered


async def test_document_list_uses_bounded_deterministic_query() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    knowledge_base_id = uuid4()

    result = await DocumentRepository(session).list_for_knowledge_base(
        knowledge_base_id,
        limit=25,
        offset=5,
    )

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = str(statement)
    assert "ORDER BY documents.created_at ASC, documents.id ASC" in rendered
    assert statement._limit_clause.value == 25
    assert statement._offset_clause.value == 5


async def test_ingestion_job_retry_query_uses_row_lock() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None

    await IngestionJobRepository(session).get(uuid4(), for_update=True)

    statement = session.scalar.await_args.args[0]
    assert "FOR UPDATE" in str(statement)


async def test_document_and_job_add_flush_without_commit() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    document = Document(
        knowledge_base_id=uuid4(),
        original_filename="file.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256="a" * 64,
        storage_key="kb/file.txt",
    )
    job = IngestionJob(document=document)

    await DocumentRepository(session).add(document)
    await IngestionJobRepository(session).add(job)

    assert session.add.call_count == 2
    assert session.flush.await_count == 2
    session.commit.assert_not_awaited()


async def test_document_chunk_list_uses_deterministic_chunk_order() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    document_id = uuid4()

    result = await DocumentChunkRepository(session).list_for_document(document_id)

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = str(statement)
    assert "document_chunks.document_id" in rendered
    assert "ORDER BY document_chunks.chunk_index ASC" in rendered


async def test_document_chunk_list_applies_and_validates_a_positive_limit() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    repository = DocumentChunkRepository(session)

    await repository.list_for_document(uuid4(), limit=50)

    statement = session.scalars.await_args.args[0]
    assert statement._limit_clause.value == 50

    with pytest.raises(ValueError, match="positive"):
        await repository.list_for_document(uuid4(), limit=0)


async def test_document_chunk_replace_deletes_and_flushes_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add_all = MagicMock()
    document_id = uuid4()
    chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="First chunk",
            token_count=2,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=1,
            normalized_text="Second chunk",
            token_count=2,
        ),
    ]

    await DocumentChunkRepository(session).replace_for_document(document_id, chunks)

    delete_statement = session.execute.await_args.args[0]
    assert "DELETE FROM document_chunks" in str(delete_statement)
    assert "document_chunks.document_id" in str(delete_statement)
    session.add_all.assert_called_once_with(chunks)
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


async def test_document_chunk_replace_rejects_mismatched_document_ids() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add_all = MagicMock()
    document_id = uuid4()
    mismatched_chunk = DocumentChunk(
        document_id=uuid4(),
        chunk_index=0,
        normalized_text="Wrong document",
        token_count=2,
    )

    with pytest.raises(ValueError, match="document_id"):
        await DocumentChunkRepository(session).replace_for_document(
            document_id,
            [mismatched_chunk],
        )

    session.execute.assert_not_awaited()
    session.add_all.assert_not_called()
    session.flush.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_claim_next_uses_due_retry_eligibility_and_skip_locked() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).claim_next(
        worker_id="worker-1",
        claimed_at=claimed_at,
        lease_expires_at=claimed_at + timedelta(minutes=5),
    )

    assert result is None
    statement = session.scalar.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.attempt_count < ingestion_jobs.max_attempts" in rendered
    assert "ingestion_jobs.next_retry_at IS NULL" in rendered
    assert "ingestion_jobs.next_retry_at <=" in rendered
    assert (
        "ORDER BY coalesce(ingestion_jobs.next_retry_at, ingestion_jobs.created_at) ASC" in rendered
    )
    assert "FOR UPDATE SKIP LOCKED" in rendered
    assert statement._limit_clause.value == 1


async def test_claim_next_updates_job_and_document_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)
    document = Document(
        knowledge_base_id=uuid4(),
        original_filename="file.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256="a" * 64,
        storage_key="kb/file.txt",
        status=DocumentStatus.PENDING.value,
    )
    job = IngestionJob(
        document=document,
        status=IngestionJobStatus.PENDING.value,
        attempt_count=1,
        max_attempts=3,
        progress_percent=40,
        next_retry_at=claimed_at,
        error_code="TRANSIENT",
        safe_error_message="Try again.",
    )
    session.scalar.return_value = job

    claimed = await IngestionJobRepository(session).claim_next(
        worker_id="worker-1",
        claimed_at=claimed_at,
        lease_expires_at=claimed_at + timedelta(minutes=5),
    )

    assert claimed is job
    assert job.status == IngestionJobStatus.PROCESSING.value
    assert job.attempt_count == 2
    assert job.progress_percent == 0
    assert job.claimed_by == "worker-1"
    assert job.claimed_at == claimed_at
    assert job.lease_expires_at == claimed_at + timedelta(minutes=5)
    assert job.next_retry_at is None
    assert job.error_code is None
    assert job.safe_error_message is None
    assert job.started_at == claimed_at
    assert job.finished_at is None
    assert document.status == DocumentStatus.PROCESSING.value
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("worker_id", "lease_delta"),
    [(" ", timedelta(minutes=5)), ("worker-1", timedelta(0))],
)
async def test_claim_next_rejects_invalid_lease_inputs(
    worker_id: str,
    lease_delta: timedelta,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)

    with pytest.raises(ValueError):
        await IngestionJobRepository(session).claim_next(
            worker_id=worker_id,
            claimed_at=claimed_at,
            lease_expires_at=claimed_at + lease_delta,
        )

    session.scalar.assert_not_awaited()


async def test_expired_lease_query_is_bounded_ordered_and_skip_locked() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    now = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).lock_expired_leases(now=now, limit=10)

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.lease_expires_at IS NOT NULL" in rendered
    assert "ingestion_jobs.lease_expires_at <=" in rendered
    assert "ORDER BY ingestion_jobs.lease_expires_at ASC, ingestion_jobs.id ASC" in rendered
    assert "FOR UPDATE SKIP LOCKED" in rendered
    assert statement._limit_clause.value == 10


async def test_expired_lease_query_rejects_a_nonpositive_limit() -> None:
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(ValueError, match="positive"):
        await IngestionJobRepository(session).lock_expired_leases(
            now=datetime(2026, 7, 28, 12, tzinfo=UTC),
            limit=0,
        )

    session.scalars.assert_not_awaited()


@pytest.mark.parametrize("for_update", [False, True])
async def test_owned_processing_query_fences_status_worker_and_expiry(
    for_update: bool,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    now = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).get_owned_processing(
        uuid4(),
        worker_id="worker-1",
        now=now,
        for_update=for_update,
    )

    assert result is None
    statement = session.scalar.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.claimed_by =" in rendered
    assert "ingestion_jobs.lease_expires_at >" in rendered
    assert ("FOR UPDATE" in rendered) is for_update
