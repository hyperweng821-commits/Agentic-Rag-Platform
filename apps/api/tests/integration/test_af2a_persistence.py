"""Opt-in PostgreSQL tests for AF-2A constraints and transaction behavior."""

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db.base import Base
from app.db.models import Document, DocumentChunk, IngestionJob, KnowledgeBase
from app.db.repositories import DocumentChunkRepository

pytestmark = pytest.mark.integration


@pytest.fixture
async def postgres_sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Create an isolated schema only when an explicit test database is provided."""
    database_url = os.getenv("AF2A_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("AF2A_TEST_DATABASE_URL is not configured")
    if not database_url.startswith("postgresql+asyncpg://"):
        pytest.fail("AF2A_TEST_DATABASE_URL must use postgresql+asyncpg://")

    schema_name = f"af2a_test_{uuid4().hex}"
    admin_engine = create_async_engine(database_url, poolclass=NullPool)
    test_engine = create_async_engine(
        database_url,
        connect_args={"server_settings": {"search_path": schema_name}},
        poolclass=NullPool,
    )
    schema_created = False
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(CreateSchema(schema_name))
        schema_created = True
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    finally:
        await test_engine.dispose()
        if schema_created:
            async with admin_engine.begin() as connection:
                await connection.execute(DropSchema(schema_name, cascade=True, if_exists=True))
        await admin_engine.dispose()


async def _add_document(
    session: AsyncSession,
    *,
    job_values: dict[str, object] | None = None,
) -> tuple[Document, IngestionJob]:
    knowledge_base = KnowledgeBase(name=f"Knowledge {uuid4()}")
    document = Document(
        knowledge_base=knowledge_base,
        original_filename="notes.txt",
        media_type="text/plain",
        size_bytes=5,
        sha256=uuid4().hex * 2,
        storage_key=f"{uuid4()}/notes.txt",
    )
    job = IngestionJob(document=document, **(job_values or {}))
    session.add(knowledge_base)
    await session.flush()
    return document, job


async def test_job_defaults_and_lease_metadata_persist_in_postgresql(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    claimed_at = datetime.now(UTC)
    lease_expires_at = claimed_at + timedelta(minutes=5)

    async with postgres_sessions() as session, session.begin():
        _, job = await _add_document(session)
        assert job.status == "pending"
        assert job.attempt_count == 0
        assert job.max_attempts == 3
        assert job.progress_percent == 0

        job.status = "processing"
        job.claimed_by = "worker-1"
        job.claimed_at = claimed_at
        job.lease_expires_at = lease_expires_at
        job_id = job.id

    async with postgres_sessions() as session:
        persisted = await session.get(IngestionJob, job_id)

        assert persisted is not None
        assert persisted.claimed_by == "worker-1"
        assert persisted.claimed_at == claimed_at
        assert persisted.lease_expires_at == lease_expires_at


async def test_failure_and_retry_metadata_persist_in_postgresql(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    next_retry_at = datetime.now(UTC) + timedelta(minutes=10)

    async with postgres_sessions() as session, session.begin():
        _, job = await _add_document(
            session,
            job_values={
                "status": "failed",
                "attempt_count": 1,
                "progress_percent": 40,
                "error_code": "PARSER_FAILED",
                "safe_error_message": "The document could not be processed.",
                "next_retry_at": next_retry_at,
            },
        )
        job_id = job.id

    async with postgres_sessions() as session:
        persisted = await session.get(IngestionJob, job_id)

        assert persisted is not None
        assert persisted.error_code == "PARSER_FAILED"
        assert persisted.safe_error_message == "The document could not be processed."
        assert persisted.next_retry_at == next_retry_at
        assert persisted.progress_percent == 40


async def test_job_checks_are_enforced_by_postgresql(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    claimed_at = datetime.now(UTC)
    valid_lease = claimed_at + timedelta(minutes=5)
    invalid_states = [
        {"attempt_count": -1},
        {"max_attempts": 0},
        {"attempt_count": 4, "max_attempts": 3},
        {"progress_percent": -1},
        {"progress_percent": 101},
        {
            "claimed_by": " ",
            "claimed_at": claimed_at,
            "lease_expires_at": valid_lease,
        },
        {
            "claimed_by": "worker-1",
            "claimed_at": None,
            "lease_expires_at": valid_lease,
        },
        {
            "claimed_by": "worker-1",
            "claimed_at": claimed_at,
            "lease_expires_at": claimed_at,
        },
    ]

    for invalid_state in invalid_states:
        async with postgres_sessions() as session:
            with pytest.raises(IntegrityError):
                await _add_document(session, job_values=invalid_state)
                await session.commit()
            await session.rollback()


async def test_chunk_checks_and_document_order_uniqueness_are_enforced(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_sessions() as session, session.begin():
        document, _ = await _add_document(session)
        document_id = document.id

    invalid_chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=-1,
            normalized_text="Text",
            token_count=1,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text=" ",
            token_count=1,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="Text",
            token_count=-1,
        ),
    ]
    for invalid_chunk in invalid_chunks:
        async with postgres_sessions() as session:
            session.add(invalid_chunk)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    async with postgres_sessions() as session:
        session.add_all(
            [
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=0,
                    normalized_text="First",
                    token_count=1,
                ),
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=0,
                    normalized_text="Duplicate",
                    token_count=1,
                ),
            ]
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


async def test_document_chunk_relationship_and_database_cascade(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_sessions() as session, session.begin():
        document, _ = await _add_document(session)
        document_id = document.id
        session.add_all(
            [
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=0,
                    normalized_text="First",
                    token_count=1,
                ),
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=1,
                    normalized_text="Second",
                    token_count=1,
                ),
            ]
        )

    async with postgres_sessions() as session, session.begin():
        persisted = await session.get(Document, document_id)

        assert persisted is not None
        chunks = await persisted.awaitable_attrs.chunks
        assert {chunk.chunk_index for chunk in chunks} == {0, 1}

    async with postgres_sessions() as session, session.begin():
        persisted = await session.get(Document, document_id)

        assert persisted is not None
        await session.delete(persisted)

    async with postgres_sessions() as session:
        chunk_count = await session.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )

        assert chunk_count == 0


async def test_chunk_replacement_rolls_back_atomically(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_sessions() as session, session.begin():
        document, _ = await _add_document(session)
        document_id = document.id
        session.add(
            DocumentChunk(
                document_id=document_id,
                chunk_index=0,
                normalized_text="Original",
                token_count=1,
            )
        )

    async with postgres_sessions() as session:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            async with session.begin():
                await DocumentChunkRepository(session).replace_for_document(
                    document_id,
                    [
                        DocumentChunk(
                            document_id=document_id,
                            chunk_index=0,
                            normalized_text="Replacement",
                            token_count=1,
                        )
                    ],
                )
                raise RuntimeError("synthetic failure")

    async with postgres_sessions() as session:
        chunks = await DocumentChunkRepository(session).list_for_document(document_id)

        assert [(chunk.chunk_index, chunk.normalized_text) for chunk in chunks] == [(0, "Original")]
