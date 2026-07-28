"""Durable AF-2B ingestion lifecycle, indexing, and rebuild workflows."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TypeVar
from uuid import UUID, uuid5

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
)
from app.db.repositories import (
    DocumentChunkRepository,
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseRepository,
)
from app.ingestion.chunking import DeterministicChunker, TextChunk
from app.ingestion.document_parsing import (
    DocumentArtifact,
    DocumentParserRegistry,
    DocumentProcessingError,
)
from app.ingestion.embeddings import (
    EmbeddingInputError,
    EmbeddingModel,
    EmbeddingRequestError,
    EmbeddingResponseError,
    EmbeddingVector,
    validate_embedding_batch,
)
from app.ingestion.storage import FileStorage, FileTooLargeError, StorageError
from app.ingestion.text_normalization import TextNormalizer
from app.ingestion.vector_store import (
    VectorRecord,
    VectorStore,
    VectorStoreConfigurationError,
    VectorStoreInputError,
    VectorStoreNotInitializedError,
    VectorStoreRequestError,
    VectorStoreResponseError,
    stable_vector_id,
)

_ResultT = TypeVar("_ResultT")
SessionFactory = Callable[[], AsyncSession]
Clock = Callable[[], datetime]


class IngestionProcessingError(Exception):
    """Base class for explicit AF-2B orchestration failures."""


class LeaseLostError(IngestionProcessingError):
    """The worker no longer owns the claimed job."""


class HeartbeatFailureError(IngestionProcessingError):
    """Unexpected lease-heartbeat code failed and must be surfaced."""


class SourceIntegrityError(IngestionProcessingError):
    """Stored source bytes no longer match their authoritative metadata."""


class ProcessingInvariantError(IngestionProcessingError):
    """A deterministic processing component violated its internal contract."""


class RebuildLimitError(IngestionProcessingError):
    """A requested rebuild exceeds its explicit work bound."""


class RebuildNotReadyError(IngestionProcessingError):
    """A document is not in a state that may be indexed."""


_EXPECTED_PROCESSING_FAILURES = (
    DocumentProcessingError,
    SourceIntegrityError,
    ProcessingInvariantError,
    FileTooLargeError,
    StorageError,
    EmbeddingInputError,
    EmbeddingRequestError,
    EmbeddingResponseError,
    VectorStoreInputError,
    VectorStoreConfigurationError,
    VectorStoreNotInitializedError,
    VectorStoreRequestError,
    VectorStoreResponseError,
    SQLAlchemyError,
)
_EXPECTED_REBUILD_FAILURES = (
    EmbeddingInputError,
    EmbeddingRequestError,
    EmbeddingResponseError,
    VectorStoreInputError,
    VectorStoreConfigurationError,
    VectorStoreNotInitializedError,
    VectorStoreRequestError,
    VectorStoreResponseError,
)


@dataclass(frozen=True, slots=True)
class ClaimedDocument:
    """Detached source metadata needed after the claim transaction commits."""

    job_id: UUID
    document_id: UUID
    knowledge_base_id: UUID
    storage_key: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class RebuildResult:
    """Bounded rebuild counts suitable for CLI reporting."""

    documents_seen: int
    documents_indexed: int
    chunks_indexed: int
    failures: tuple[RebuildFailure, ...] = ()


@dataclass(frozen=True, slots=True)
class RebuildFailure:
    """One safe per-document rebuild failure."""

    document_id: UUID
    code: str
    safe_message: str


@dataclass(frozen=True, slots=True)
class _Failure:
    code: str
    safe_message: str
    retryable: bool


class _LeaseHeartbeat:
    """Renew one lease through short independent transactions."""

    def __init__(
        self,
        *,
        interval_seconds: float,
        renew: Callable[[], Awaitable[bool]],
    ) -> None:
        self._interval_seconds = interval_seconds
        self._renew = renew
        self._stop = asyncio.Event()
        self.lost = asyncio.Event()
        self._error: Exception | None = None
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            while not self._stop.is_set():
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self._interval_seconds)
                    return
                except TimeoutError:
                    pass
                try:
                    renewed = await self._renew()
                except SQLAlchemyError as exc:
                    self._error = exc
                    self.lost.set()
                    return
                except Exception as exc:
                    self._error = HeartbeatFailureError("Unexpected lease-heartbeat failure.")
                    self._error.__cause__ = exc
                    self.lost.set()
                    return
                if not renewed:
                    self.lost.set()
                    return
        except asyncio.CancelledError:
            # ``stop`` owns this internal task and cancels it so shutdown never
            # waits behind an in-progress database renewal. Caller cancellation
            # is still propagated by the processing task.
            return

    def ensure_owned(self) -> None:
        if not self.lost.is_set():
            return
        if isinstance(self._error, HeartbeatFailureError):
            raise self._error
        if self._error is not None:
            raise LeaseLostError("The job lease could not be renewed.") from self._error
        raise LeaseLostError("The job lease is no longer owned by this worker.")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is None:
            return
        if not self._task.done():
            self._task.cancel()
        await self._task


class IngestionProcessingService:
    """Process and rebuild documents without holding database transactions over I/O."""

    def __init__(
        self,
        *,
        session_factory: SessionFactory,
        storage: FileStorage,
        parser_registry: DocumentParserRegistry,
        normalizer: TextNormalizer,
        chunker: DeterministicChunker,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
        worker_id: str,
        lease_duration: timedelta,
        retry_delay: timedelta,
        source_max_bytes: int,
        rebuild_batch_size: int,
        clock: Clock = lambda: datetime.now(UTC),
    ) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id must not be blank")
        if lease_duration.total_seconds() <= 0:
            raise ValueError("lease_duration must be positive")
        if retry_delay.total_seconds() < 0:
            raise ValueError("retry_delay must be non-negative")
        if source_max_bytes < 1:
            raise ValueError("source_max_bytes must be positive")
        if rebuild_batch_size < 1:
            raise ValueError("rebuild_batch_size must be positive")
        self._session_factory = session_factory
        self._storage = storage
        self._parser_registry = parser_registry
        self._normalizer = normalizer
        self._chunker = chunker
        self._embedding_model = embedding_model
        self._vector_store = vector_store
        self._worker_id = worker_id
        self._lease_duration = lease_duration
        self._retry_delay = retry_delay
        self._source_max_bytes = source_max_bytes
        self._rebuild_batch_size = rebuild_batch_size
        self._clock = clock
        self._initialized = False
        self._initialize_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the derived index once before claiming durable work."""
        async with self._initialize_lock:
            if self._initialized:
                return
            await self._vector_store.initialize(
                model_id=self._embedding_model.model_id,
                dimension=self._embedding_model.dimension,
            )
            self._initialized = True

    async def close(self) -> None:
        """Close owned adapter resources."""
        try:
            await self._embedding_model.close()
        finally:
            await self._vector_store.close()

    async def recover_expired_leases(self, *, limit: int) -> int:
        """Requeue or fail a bounded set of expired processing attempts."""
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            jobs = await IngestionJobRepository(session).lock_expired_leases(
                now=now,
                limit=limit,
            )
            for job in jobs:
                self._clear_lease(job)
                job.error_code = "LEASE_EXPIRED"
                job.safe_error_message = "The previous processing attempt did not finish."
                if job.attempt_count < job.max_attempts:
                    job.status = IngestionJobStatus.PENDING.value
                    job.document.status = DocumentStatus.PENDING.value
                    job.progress_percent = 0
                    job.next_retry_at = now + self._retry_delay
                    job.started_at = None
                    job.finished_at = None
                else:
                    job.status = IngestionJobStatus.FAILED.value
                    job.document.status = DocumentStatus.FAILED.value
                    job.next_retry_at = None
                    job.finished_at = now
            await session.flush()
            return len(jobs)

    async def process_next(self, *, recovery_limit: int = 32) -> bool:
        """Recover expired leases and process at most one due job."""
        await self.initialize()
        await self.recover_expired_leases(limit=recovery_limit)
        claimed = await self._claim_next()
        if claimed is None:
            return False

        heartbeat = _LeaseHeartbeat(
            interval_seconds=max(self._lease_duration.total_seconds() / 3, 0.01),
            renew=lambda: self._renew_lease(claimed.job_id),
        )
        heartbeat.start()
        try:
            content = await self._with_lease(
                heartbeat,
                self._read_and_verify_source(claimed),
            )
            chunks = await self._with_lease(
                heartbeat,
                asyncio.to_thread(self._parse_and_chunk, claimed, content),
            )
            durable_chunks = await self._replace_chunks(claimed, chunks)
            vectors = await self._with_lease(
                heartbeat,
                self._embed_chunks(claimed, durable_chunks),
            )
            await self._with_lease(
                heartbeat,
                self._replace_vectors(claimed.document_id, vectors),
            )
            await heartbeat.stop()
            heartbeat.ensure_owned()
            await self._complete_success(claimed.job_id)
        except asyncio.CancelledError as cancellation:
            await heartbeat.stop()
            try:
                await self._complete_failure(
                    claimed.job_id,
                    _Failure(
                        code="PROCESSING_CANCELLED",
                        safe_message="Document processing was interrupted.",
                        retryable=True,
                    ),
                )
            except SQLAlchemyError:
                cancellation.add_note(
                    "The cancellation state transition failed; lease-expiry recovery is required."
                )
            raise
        except LeaseLostError:
            await heartbeat.stop()
        except _EXPECTED_PROCESSING_FAILURES as exc:
            await heartbeat.stop()
            await self._complete_failure(claimed.job_id, self._classify_failure(exc))
        except Exception:
            await heartbeat.stop()
            try:
                await self._complete_failure(
                    claimed.job_id,
                    _Failure(
                        code="INGESTION_FAILED",
                        safe_message="The document could not be processed.",
                        retryable=True,
                    ),
                )
            finally:
                raise
        return True

    async def rebuild_document(
        self,
        document_id: UUID,
        *,
        max_chunks: int,
    ) -> RebuildResult:
        """Replace one document's derived vectors from bounded PostgreSQL chunks."""
        if max_chunks < 1:
            raise ValueError("max_chunks must be positive")
        await self.initialize()
        document, chunks = await self._load_rebuild_document(
            document_id,
            max_chunks=max_chunks,
        )
        indexed_chunks = 0
        try:
            records = await self._records_for_chunks(document, chunks)
            await self._vector_store.delete_by_document(document_id)
            for batch in self._batches(records):
                await self._vector_store.upsert(batch)
                indexed_chunks += len(batch)
        except _EXPECTED_REBUILD_FAILURES as exc:
            failure = self._classify_failure(exc)
            return RebuildResult(
                documents_seen=1,
                documents_indexed=0,
                chunks_indexed=indexed_chunks,
                failures=(
                    RebuildFailure(
                        document_id=document_id,
                        code=failure.code,
                        safe_message=failure.safe_message,
                    ),
                ),
            )
        return RebuildResult(
            documents_seen=1,
            documents_indexed=1,
            chunks_indexed=len(records),
        )

    async def rebuild_knowledge_base(
        self,
        knowledge_base_id: UUID,
        *,
        max_documents: int,
        max_chunks_per_document: int,
    ) -> RebuildResult:
        """Rebuild completed documents without racing active ingestion work."""
        if max_documents < 1 or max_chunks_per_document < 1:
            raise ValueError("rebuild limits must be positive")
        await self.initialize()
        async with self._session_factory() as session, session.begin():
            if await KnowledgeBaseRepository(session).get(knowledge_base_id) is None:
                raise RebuildNotReadyError("The knowledge base does not exist.")
            documents = await DocumentRepository(session).list_for_knowledge_base(
                knowledge_base_id,
                limit=max_documents + 1,
                offset=0,
            )
        if len(documents) > max_documents:
            raise RebuildLimitError("The knowledge-base rebuild exceeds max_documents.")

        indexed_documents = 0
        indexed_chunks = 0
        failures: list[RebuildFailure] = []
        for document in documents:
            if document.status != DocumentStatus.COMPLETED.value:
                failures.append(
                    RebuildFailure(
                        document_id=document.id,
                        code="REBUILD_NOT_READY",
                        safe_message="Only completed documents can be rebuilt.",
                    )
                )
                continue
            try:
                result = await self.rebuild_document(
                    document.id,
                    max_chunks=max_chunks_per_document,
                )
            except (RebuildLimitError, RebuildNotReadyError) as exc:
                failures.append(
                    RebuildFailure(
                        document_id=document.id,
                        code=type(exc).__name__.upper(),
                        safe_message=str(exc),
                    )
                )
                continue
            indexed_documents += result.documents_indexed
            indexed_chunks += result.chunks_indexed
            failures.extend(result.failures)
        return RebuildResult(
            documents_seen=len(documents),
            documents_indexed=indexed_documents,
            chunks_indexed=indexed_chunks,
            failures=tuple(failures),
        )

    async def _claim_next(self) -> ClaimedDocument | None:
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            job = await IngestionJobRepository(session).claim_next(
                worker_id=self._worker_id,
                claimed_at=now,
                lease_expires_at=now + self._lease_duration,
            )
            if job is None:
                return None
            return self._claimed_document(job)

    @staticmethod
    def _claimed_document(job: IngestionJob) -> ClaimedDocument:
        document = job.document
        return ClaimedDocument(
            job_id=job.id,
            document_id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            storage_key=document.storage_key,
            filename=document.original_filename,
            media_type=document.media_type,
            size_bytes=document.size_bytes,
            sha256=document.sha256,
        )

    async def _renew_lease(self, job_id: UUID) -> bool:
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            job = await IngestionJobRepository(session).get_owned_processing(
                job_id,
                worker_id=self._worker_id,
                now=now,
                for_update=True,
            )
            if job is None:
                return False
            job.lease_expires_at = now + self._lease_duration
            await session.flush()
            return True

    async def _read_and_verify_source(self, claimed: ClaimedDocument) -> bytes:
        content = await self._storage.read(
            claimed.storage_key,
            max_bytes=min(self._source_max_bytes, claimed.size_bytes),
        )
        if len(content) != claimed.size_bytes:
            raise SourceIntegrityError("Stored source size does not match document metadata.")
        digest = hashlib.sha256(content).hexdigest()
        if digest != claimed.sha256:
            raise SourceIntegrityError("Stored source digest does not match document metadata.")
        return content

    def _parse_and_chunk(
        self,
        claimed: ClaimedDocument,
        content: bytes,
    ) -> tuple[TextChunk, ...]:
        artifact = DocumentArtifact(
            content=content,
            media_type=claimed.media_type,
            filename=claimed.filename,
        )
        parsed = self._parser_registry.parse(artifact)
        normalized = self._normalizer.normalize(parsed)
        chunks = self._chunker.chunk(normalized)
        if not chunks:
            raise ProcessingInvariantError("Chunking produced no durable text.")
        for expected_index, chunk in enumerate(chunks):
            expected_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
            if chunk.chunk_index != expected_index or chunk.content_hash != expected_hash:
                raise ProcessingInvariantError("Chunking produced inconsistent metadata.")
        return chunks

    async def _replace_chunks(
        self,
        claimed: ClaimedDocument,
        chunks: Sequence[TextChunk],
    ) -> list[DocumentChunk]:
        durable_chunks = [
            DocumentChunk(
                id=uuid5(
                    claimed.document_id,
                    f"{chunk.chunk_index}:{chunk.content_hash}",
                ),
                document_id=claimed.document_id,
                chunk_index=chunk.chunk_index,
                normalized_text=chunk.text,
                token_count=chunk.token_count,
                content_sha256=chunk.content_hash,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                page_start=min(chunk.page_numbers) if chunk.page_numbers else None,
                page_end=max(chunk.page_numbers) if chunk.page_numbers else None,
            )
            for chunk in chunks
        ]
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            job = await IngestionJobRepository(session).get_owned_processing(
                claimed.job_id,
                worker_id=self._worker_id,
                now=now,
                for_update=True,
            )
            if job is None:
                raise LeaseLostError("The chunk replacement no longer owns its job lease.")
            await DocumentChunkRepository(session).replace_for_document(
                claimed.document_id,
                durable_chunks,
            )
            job.progress_percent = 50
            job.lease_expires_at = now + self._lease_duration
            await session.flush()
        return durable_chunks

    async def _embed_chunks(
        self,
        claimed: ClaimedDocument,
        chunks: Sequence[DocumentChunk],
    ) -> list[VectorRecord]:
        vectors = await self._embedding_model.embed([chunk.normalized_text for chunk in chunks])
        validated = validate_embedding_batch(
            [chunk.normalized_text for chunk in chunks],
            vectors,
            dimension=self._embedding_model.dimension,
        )
        return self._make_vector_records(claimed.knowledge_base_id, chunks, validated)

    @staticmethod
    def _make_vector_records(
        knowledge_base_id: UUID,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[EmbeddingVector],
    ) -> list[VectorRecord]:
        records: list[VectorRecord] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            if chunk.content_sha256 is None:
                raise ProcessingInvariantError("A durable chunk has no content digest.")
            records.append(
                VectorRecord(
                    vector_id=stable_vector_id(chunk.id),
                    embedding=embedding,
                    knowledge_base_id=knowledge_base_id,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    normalized_text=chunk.normalized_text,
                    content_hash=chunk.content_sha256,
                )
            )
        return records

    async def _replace_vectors(
        self,
        document_id: UUID,
        records: Sequence[VectorRecord],
    ) -> None:
        await self._vector_store.delete_by_document(document_id)
        for batch in self._batches(records):
            await self._vector_store.upsert(batch)

    async def _complete_success(self, job_id: UUID) -> None:
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            job = await IngestionJobRepository(session).get_owned_processing(
                job_id,
                worker_id=self._worker_id,
                now=now,
                for_update=True,
            )
            if job is None:
                raise LeaseLostError("The successful result no longer owns its job lease.")
            job.status = IngestionJobStatus.COMPLETED.value
            job.document.status = DocumentStatus.COMPLETED.value
            job.progress_percent = 100
            self._clear_lease(job)
            job.next_retry_at = None
            job.error_code = None
            job.safe_error_message = None
            job.finished_at = now
            await session.flush()

    async def _complete_failure(self, job_id: UUID, failure: _Failure) -> None:
        now = self._clock()
        async with self._session_factory() as session, session.begin():
            job = await IngestionJobRepository(session).get_owned_processing(
                job_id,
                worker_id=self._worker_id,
                now=now,
                for_update=True,
            )
            if job is None:
                return
            self._clear_lease(job)
            job.error_code = failure.code
            job.safe_error_message = failure.safe_message
            if failure.retryable and job.attempt_count < job.max_attempts:
                job.status = IngestionJobStatus.PENDING.value
                job.document.status = DocumentStatus.PENDING.value
                job.progress_percent = 0
                job.next_retry_at = now + self._retry_delay
                job.started_at = None
                job.finished_at = None
            else:
                job.status = IngestionJobStatus.FAILED.value
                job.document.status = DocumentStatus.FAILED.value
                job.next_retry_at = None
                job.finished_at = now
            await session.flush()

    @staticmethod
    def _clear_lease(job: IngestionJob) -> None:
        job.claimed_by = None
        job.claimed_at = None
        job.lease_expires_at = None

    async def _load_rebuild_document(
        self,
        document_id: UUID,
        *,
        max_chunks: int,
    ) -> tuple[Document, list[DocumentChunk]]:
        async with self._session_factory() as session, session.begin():
            document = await DocumentRepository(session).get(document_id)
            if document is None:
                raise RebuildNotReadyError("The document does not exist.")
            if document.status != DocumentStatus.COMPLETED.value:
                raise RebuildNotReadyError("Only completed documents can be rebuilt.")
            chunks = await DocumentChunkRepository(session).list_for_document(
                document_id,
                limit=max_chunks + 1,
            )
            if len(chunks) > max_chunks:
                raise RebuildLimitError("The document rebuild exceeds max_chunks.")
            if not chunks:
                raise RebuildNotReadyError("The completed document has no durable chunks.")
            if any(chunk.content_sha256 is None for chunk in chunks):
                raise RebuildNotReadyError(
                    "The document contains legacy chunks without AF-2B provenance."
                )
            return document, chunks

    async def _records_for_chunks(
        self,
        document: Document,
        chunks: Sequence[DocumentChunk],
    ) -> list[VectorRecord]:
        records: list[VectorRecord] = []
        for batch in self._batches(chunks):
            texts = [chunk.normalized_text for chunk in batch]
            vectors = await self._embedding_model.embed(texts)
            validated = validate_embedding_batch(
                texts,
                vectors,
                dimension=self._embedding_model.dimension,
            )
            records.extend(
                self._make_vector_records(
                    document.knowledge_base_id,
                    batch,
                    validated,
                )
            )
        return records

    def _batches(self, values: Sequence[_ResultT]) -> list[Sequence[_ResultT]]:
        return [
            values[start : start + self._rebuild_batch_size]
            for start in range(0, len(values), self._rebuild_batch_size)
        ]

    async def _with_lease(
        self,
        heartbeat: _LeaseHeartbeat,
        operation: Coroutine[object, object, _ResultT],
    ) -> _ResultT:
        work = asyncio.create_task(operation)
        lease_lost = asyncio.create_task(heartbeat.lost.wait())
        try:
            heartbeat.ensure_owned()
            await asyncio.wait(
                {work, lease_lost},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if heartbeat.lost.is_set():
                work.cancel()
                with suppress(asyncio.CancelledError):
                    await work
                heartbeat.ensure_owned()
            lease_lost.cancel()
            with suppress(asyncio.CancelledError):
                await lease_lost
            result = await work
            heartbeat.ensure_owned()
            return result
        finally:
            if not work.done():
                work.cancel()
            if not lease_lost.done():
                lease_lost.cancel()
            await asyncio.gather(work, lease_lost, return_exceptions=True)

    @staticmethod
    def _classify_failure(exc: Exception) -> _Failure:
        if isinstance(exc, SourceIntegrityError):
            return _Failure(
                code="SOURCE_INTEGRITY_FAILED",
                safe_message="The stored document failed integrity validation.",
                retryable=False,
            )
        if isinstance(exc, ProcessingInvariantError):
            return _Failure(
                code="PROCESSING_INVARIANT_FAILED",
                safe_message="The document processor produced inconsistent output.",
                retryable=False,
            )
        if isinstance(exc, DocumentProcessingError):
            return _Failure(
                code="DOCUMENT_PROCESSING_FAILED",
                safe_message="The document could not be converted into searchable text.",
                retryable=False,
            )
        if isinstance(exc, FileTooLargeError):
            return _Failure(
                code="STORED_DOCUMENT_TOO_LARGE",
                safe_message="The stored document exceeds the processing limit.",
                retryable=False,
            )
        if isinstance(exc, StorageError):
            return _Failure(
                code="STORAGE_READ_FAILED",
                safe_message="The stored document is temporarily unavailable.",
                retryable=True,
            )
        if isinstance(exc, SQLAlchemyError):
            return _Failure(
                code="DATABASE_OPERATION_FAILED",
                safe_message="The document state could not be persisted.",
                retryable=True,
            )
        if isinstance(
            exc,
            (
                EmbeddingInputError,
                VectorStoreInputError,
                VectorStoreConfigurationError,
            ),
        ):
            return _Failure(
                code="INGESTION_CONFIGURATION_FAILED",
                safe_message="The ingestion pipeline configuration is invalid.",
                retryable=False,
            )
        if isinstance(
            exc,
            (
                EmbeddingRequestError,
                EmbeddingResponseError,
                VectorStoreNotInitializedError,
                VectorStoreRequestError,
                VectorStoreResponseError,
            ),
        ):
            return _Failure(
                code="INGESTION_DEPENDENCY_FAILED",
                safe_message="A document-processing dependency is temporarily unavailable.",
                retryable=True,
            )
        return _Failure(
            code="INGESTION_FAILED",
            safe_message="The document could not be processed.",
            retryable=True,
        )
