"""Focused tests for AF-1 and AF-2A repository query and flush behavior."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk, IngestionJob, KnowledgeBase
from app.db.repositories import (
    DocumentChunkRepository,
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseRepository,
)


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
