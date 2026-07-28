"""Explicit SQLAlchemy queries for AF-1 intake and AF-2 ingestion."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
)


class KnowledgeBaseRepository:
    """Persistence operations for knowledge bases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, knowledge_base: KnowledgeBase) -> None:
        self._session.add(knowledge_base)
        await self._session.flush()

    async def get(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        return await self._session.get(KnowledgeBase, knowledge_base_id)

    async def list(self, *, limit: int, offset: int) -> list[KnowledgeBase]:
        statement = (
            select(KnowledgeBase)
            .order_by(KnowledgeBase.created_at.asc(), KnowledgeBase.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.scalars(statement)).all())


class DocumentRepository:
    """Persistence operations for document metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: Document) -> None:
        self._session.add(document)
        await self._session.flush()

    async def get(self, document_id: UUID) -> Document | None:
        statement = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.ingestion_job))
        )
        document: Document | None = await self._session.scalar(statement)
        return document

    async def get_by_digest(
        self,
        *,
        knowledge_base_id: UUID,
        sha256: str,
    ) -> Document | None:
        statement = (
            select(Document)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.sha256 == sha256,
            )
            .options(selectinload(Document.ingestion_job))
        )
        document: Document | None = await self._session.scalar(statement)
        return document

    async def list_for_knowledge_base(
        self,
        knowledge_base_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Document]:
        statement: Select[tuple[Document]] = (
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(Document.created_at.asc(), Document.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.scalars(statement)).all())


class DocumentChunkRepository:
    """Persistence operations for ordered, PostgreSQL-authoritative chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_document(
        self,
        document_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        if limit is not None:
            if limit < 1:
                raise ValueError("limit must be positive")
            statement = statement.limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def replace_for_document(
        self,
        document_id: UUID,
        chunks: Sequence[DocumentChunk],
    ) -> None:
        if any(chunk.document_id != document_id for chunk in chunks):
            raise ValueError("Every replacement chunk must match the target document_id.")

        await self._session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        self._session.add_all(list(chunks))
        await self._session.flush()


class IngestionJobRepository:
    """Persistence operations for one durable job per document."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, job: IngestionJob) -> None:
        self._session.add(job)
        await self._session.flush()

    async def get(self, job_id: UUID, *, for_update: bool = False) -> IngestionJob | None:
        statement = (
            select(IngestionJob)
            .where(IngestionJob.id == job_id)
            .options(selectinload(IngestionJob.document))
        )
        if for_update:
            statement = statement.with_for_update()
        job: IngestionJob | None = await self._session.scalar(statement)
        return job

    async def claim_next(
        self,
        *,
        worker_id: str,
        claimed_at: datetime,
        lease_expires_at: datetime,
    ) -> IngestionJob | None:
        """Claim one due pending job while concurrent workers skip its row lock."""
        if not worker_id.strip():
            raise ValueError("worker_id must not be blank")
        if lease_expires_at <= claimed_at:
            raise ValueError("lease_expires_at must be later than claimed_at")

        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.status == IngestionJobStatus.PENDING.value,
                IngestionJob.attempt_count < IngestionJob.max_attempts,
                or_(
                    IngestionJob.next_retry_at.is_(None),
                    IngestionJob.next_retry_at <= claimed_at,
                ),
            )
            .options(selectinload(IngestionJob.document))
            .order_by(
                func.coalesce(IngestionJob.next_retry_at, IngestionJob.created_at).asc(),
                IngestionJob.created_at.asc(),
                IngestionJob.id.asc(),
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job: IngestionJob | None = await self._session.scalar(statement)
        if job is None:
            return None

        job.status = IngestionJobStatus.PROCESSING.value
        job.attempt_count += 1
        job.progress_percent = 0
        job.claimed_by = worker_id
        job.claimed_at = claimed_at
        job.lease_expires_at = lease_expires_at
        job.next_retry_at = None
        job.error_code = None
        job.safe_error_message = None
        job.started_at = claimed_at
        job.finished_at = None
        job.document.status = DocumentStatus.PROCESSING.value
        await self._session.flush()
        return job

    async def lock_expired_leases(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[IngestionJob]:
        """Lock a bounded set of expired jobs without waiting on other recoverers."""
        if limit < 1:
            raise ValueError("limit must be positive")
        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.status == IngestionJobStatus.PROCESSING.value,
                IngestionJob.lease_expires_at.is_not(None),
                IngestionJob.lease_expires_at <= now,
            )
            .options(selectinload(IngestionJob.document))
            .order_by(IngestionJob.lease_expires_at.asc(), IngestionJob.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list((await self._session.scalars(statement)).all())

    async def get_owned_processing(
        self,
        job_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        for_update: bool = False,
    ) -> IngestionJob | None:
        """Read an unexpired processing job only when the caller still owns its lease."""
        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.id == job_id,
                IngestionJob.status == IngestionJobStatus.PROCESSING.value,
                IngestionJob.claimed_by == worker_id,
                IngestionJob.lease_expires_at > now,
            )
            .options(selectinload(IngestionJob.document))
        )
        if for_update:
            statement = statement.with_for_update()
        job: IngestionJob | None = await self._session.scalar(statement)
        return job
