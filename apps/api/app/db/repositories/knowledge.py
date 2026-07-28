"""Explicit SQLAlchemy queries for AF-1 and AF-2A durable records."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Document, DocumentChunk, IngestionJob, KnowledgeBase


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

    async def list_for_document(self, document_id: UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
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
