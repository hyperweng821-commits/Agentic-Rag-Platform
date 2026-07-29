"""Opt-in PostgreSQL tests for AF-2 durable schema and claim behavior."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import func, inspect, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.db.models import Document, DocumentChunk, IngestionJob, KnowledgeBase
from app.db.repositories import DocumentChunkRepository, IngestionJobRepository

pytestmark = pytest.mark.integration


def _run_revision(
    connection: Connection,
    revision: str,
    direction: Literal["upgrade", "downgrade"],
) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    revision_script = scripts.get_revision(revision)
    migration = cast(Callable[[], None], getattr(revision_script.module, direction))
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        migration()


def _upgrade_through_af2b(connection: Connection) -> None:
    for revision in ("20260727_0001", "20260728_0002", "20260728_0003"):
        _run_revision(connection, revision, "upgrade")


def _chunk_schema(connection: Connection) -> tuple[set[str], set[str]]:
    inspector = inspect(connection)
    columns = {column["name"] for column in inspector.get_columns("document_chunks")}
    constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("document_chunks")
        if constraint["name"] is not None
    }
    return columns, constraints


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
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="Text",
            token_count=1,
            content_sha256="A" * 64,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="Text",
            token_count=1,
            start_offset=0,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="Text",
            token_count=1,
            start_offset=1,
            end_offset=1,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="Text",
            token_count=1,
            page_start=0,
            page_end=1,
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
                await DocumentChunkRepository(session).replace_for_document_internal(
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
        chunks = await DocumentChunkRepository(session).list_for_document_internal(document_id)

        assert [(chunk.chunk_index, chunk.normalized_text) for chunk in chunks] == [(0, "Original")]


async def test_second_worker_skips_the_only_locked_job(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    async with postgres_sessions() as session, session.begin():
        _, job = await _add_document(session)
        job_id = job.id

    release_claim = asyncio.Event()
    first_claimed = asyncio.Event()

    async def claim_and_hold() -> UUID:
        async with postgres_sessions() as session, session.begin():
            claimed = await IngestionJobRepository(session).claim_next_internal(
                worker_id="worker-1",
                claimed_at=now,
                lease_expires_at=now + timedelta(minutes=5),
            )
            assert claimed is not None
            first_claimed.set()
            await release_claim.wait()
            return claimed.id

    first_task = asyncio.create_task(claim_and_hold())
    try:
        await asyncio.wait_for(first_claimed.wait(), timeout=5)
        async with postgres_sessions() as session, session.begin():
            second_claim = await IngestionJobRepository(session).claim_next_internal(
                worker_id="worker-2",
                claimed_at=now,
                lease_expires_at=now + timedelta(minutes=5),
            )
        assert second_claim is None
    finally:
        release_claim.set()
        first_job_id = await first_task

    assert first_job_id == job_id


async def test_concurrent_workers_skip_a_locked_claim_without_sleeping(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    async with postgres_sessions() as session, session.begin():
        _, first_job = await _add_document(
            session,
            job_values={"created_at": now - timedelta(seconds=2)},
        )
        _, second_job = await _add_document(
            session,
            job_values={"created_at": now - timedelta(seconds=1)},
        )
        expected_job_ids = {first_job.id, second_job.id}

    release_claims = asyncio.Event()
    first_claimed = asyncio.Event()
    second_claimed = asyncio.Event()

    async def claim_and_hold(worker_id: str, claimed: asyncio.Event) -> UUID:
        async with postgres_sessions() as session, session.begin():
            job = await IngestionJobRepository(session).claim_next_internal(
                worker_id=worker_id,
                claimed_at=now,
                lease_expires_at=now + timedelta(minutes=5),
            )
            assert job is not None
            job_id = job.id
            claimed.set()
            await release_claims.wait()
            return job_id

    first_task = asyncio.create_task(claim_and_hold("worker-1", first_claimed))
    second_task: asyncio.Task[UUID] | None = None
    try:
        await asyncio.wait_for(first_claimed.wait(), timeout=5)
        second_task = asyncio.create_task(claim_and_hold("worker-2", second_claimed))
        await asyncio.wait_for(second_claimed.wait(), timeout=5)
    finally:
        release_claims.set()

    assert second_task is not None
    claimed_job_ids = set(await asyncio.gather(first_task, second_task))

    assert claimed_job_ids == expected_job_ids
    async with postgres_sessions() as session:
        jobs = [await session.get(IngestionJob, job_id) for job_id in claimed_job_ids]

    assert {job.claimed_by for job in jobs if job is not None} == {"worker-1", "worker-2"}
    assert {job.status for job in jobs if job is not None} == {"processing"}


async def test_claim_next_selects_a_due_retry_and_leaves_a_future_retry_pending(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    async with postgres_sessions() as session, session.begin():
        _, due_job = await _add_document(
            session,
            job_values={"next_retry_at": now - timedelta(seconds=1)},
        )
        _, future_job = await _add_document(
            session,
            job_values={"next_retry_at": now + timedelta(minutes=5)},
        )
        due_job_id = due_job.id
        future_job_id = future_job.id

    async with postgres_sessions() as session, session.begin():
        claimed = await IngestionJobRepository(session).claim_next_internal(
            worker_id="worker-1",
            claimed_at=now,
            lease_expires_at=now + timedelta(minutes=5),
        )

        assert claimed is not None
        assert claimed.id == due_job_id

    async with postgres_sessions() as session:
        future = await session.get(IngestionJob, future_job_id)

    assert future is not None
    assert future.status == "pending"
    assert future.next_retry_at == now + timedelta(minutes=5)


async def test_owned_processing_lookup_fences_worker_expiry_and_status(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    lease_expires_at = now + timedelta(minutes=5)
    async with postgres_sessions() as session, session.begin():
        _, job = await _add_document(session)
        job_id = job.id

    async with postgres_sessions() as session, session.begin():
        claimed = await IngestionJobRepository(session).claim_next_internal(
            worker_id="worker-1",
            claimed_at=now,
            lease_expires_at=lease_expires_at,
        )
        assert claimed is not None
        assert claimed.id == job_id

    async with postgres_sessions() as session, session.begin():
        repository = IngestionJobRepository(session)

        owned = await repository.get_owned_processing_internal(
            job_id,
            worker_id="worker-1",
            now=now,
            for_update=True,
        )
        wrong_worker = await repository.get_owned_processing_internal(
            job_id,
            worker_id="worker-2",
            now=now,
        )
        expired = await repository.get_owned_processing_internal(
            job_id,
            worker_id="worker-1",
            now=lease_expires_at,
        )

        assert owned is not None
        assert wrong_worker is None
        assert expired is None

        owned.status = "pending"
        await session.flush()
        wrong_status = await repository.get_owned_processing_internal(
            job_id,
            worker_id="worker-1",
            now=now,
        )

        assert wrong_status is None


async def test_af2b_migration_round_trips_in_isolated_postgresql_schema(
    postgres_migration_engine: AsyncEngine,
) -> None:
    provenance_columns = {
        "content_sha256",
        "start_offset",
        "end_offset",
        "page_start",
        "page_end",
    }
    provenance_constraints = {
        "ck_document_chunks_valid_content_sha256",
        "ck_document_chunks_valid_source_offsets",
        "ck_document_chunks_valid_page_range",
    }

    async with postgres_migration_engine.begin() as connection:
        await connection.run_sync(_upgrade_through_af2b)
        columns, constraints = await connection.run_sync(_chunk_schema)

        assert provenance_columns <= columns
        assert provenance_constraints <= constraints

        await connection.run_sync(
            lambda sync_connection: _run_revision(
                sync_connection,
                "20260728_0003",
                "downgrade",
            )
        )
        columns, constraints = await connection.run_sync(_chunk_schema)

        assert provenance_columns.isdisjoint(columns)
        assert provenance_constraints.isdisjoint(constraints)
        assert {"id", "document_id", "chunk_index", "normalized_text", "token_count"} <= columns

        await connection.run_sync(
            lambda sync_connection: _run_revision(
                sync_connection,
                "20260728_0003",
                "upgrade",
            )
        )
        columns, constraints = await connection.run_sync(_chunk_schema)

        assert provenance_columns <= columns
        assert provenance_constraints <= constraints
