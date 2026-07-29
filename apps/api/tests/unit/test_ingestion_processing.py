"""Deterministic AF-2B lifecycle, transaction-boundary, and rebuild tests."""

import asyncio
import hashlib
import threading
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import cast
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy.exc import SQLAlchemyError

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
from app.ingestion.chunking import ChunkingConfig, DeterministicChunker
from app.ingestion.document_parsing import (
    DocumentParserRegistry,
    ParsedDocument,
    ParsedSection,
    create_default_parser_registry,
)
from app.ingestion.embeddings import EmbeddingRequestError, EmbeddingVector
from app.ingestion.storage import AsyncReadable, StoredFile
from app.ingestion.text_normalization import TextNormalizer
from app.ingestion.vector_store import VectorRecord, VectorStoreRequestError, stable_vector_id
from app.services.ingestion_processing import (
    IngestionProcessingService,
    SessionFactory,
)

_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


class _TransactionState:
    def __init__(self) -> None:
        self.active = 0
        self.sessions_opened = 0


class _Transaction:
    def __init__(self, state: _TransactionState) -> None:
        self._state = state

    async def __aenter__(self) -> None:
        self._state.active += 1

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._state.active -= 1


class _Session:
    def __init__(self, state: _TransactionState) -> None:
        self._state = state

    async def __aenter__(self) -> "_Session":
        self._state.sessions_opened += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def begin(self) -> _Transaction:
        return _Transaction(self._state)

    async def flush(self) -> None:
        return None


class _Storage:
    def __init__(
        self,
        content: bytes,
        state: _TransactionState,
        *,
        started: asyncio.Event | None = None,
        release: asyncio.Event | None = None,
        finished: asyncio.Event | None = None,
        error: Exception | None = None,
    ) -> None:
        self._content = content
        self._state = state
        self._started = started
        self._release = release
        self._finished = finished
        self._error = error

    def replace_content(self, content: bytes) -> None:
        self._content = content

    async def store(
        self,
        source: AsyncReadable,
        *,
        storage_key: str,
        max_bytes: int,
    ) -> StoredFile:
        raise NotImplementedError

    async def delete(self, storage_key: str) -> None:
        return None

    async def read(self, storage_key: str, *, max_bytes: int) -> bytes:
        assert self._state.active == 0
        if self._started is not None:
            self._started.set()
        try:
            if self._release is not None:
                await self._release.wait()
            if self._error is not None:
                raise self._error
            assert len(self._content) <= max_bytes
            return self._content
        finally:
            if self._finished is not None:
                self._finished.set()


class _Embedding:
    model_id = "test-embedding"
    dimension = 2

    def __init__(
        self,
        state: _TransactionState,
        *,
        error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self._state = state
        self._error = error
        self._close_error = close_error
        self.closed = False

    async def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        assert self._state.active == 0
        if self._error is not None:
            raise self._error
        return [(float(index), float(index + 1)) for index, _ in enumerate(texts)]

    async def close(self) -> None:
        self.closed = True
        if self._close_error is not None:
            raise self._close_error


class _VectorStore:
    def __init__(
        self,
        state: _TransactionState,
        *,
        fail_on_upsert: int | None = None,
    ) -> None:
        self._state = state
        self._fail_on_upsert = fail_on_upsert
        self.upsert_calls = 0
        self.deleted_documents: list[UUID] = []
        self.records: list[VectorRecord] = []
        self.initialized = False
        self.closed = False

    async def initialize(self, *, model_id: str, dimension: int) -> None:
        assert self._state.active == 0
        self.initialized = True

    async def upsert(self, records: Sequence[VectorRecord]) -> None:
        assert self._state.active == 0
        self.upsert_calls += 1
        if self.upsert_calls == self._fail_on_upsert:
            raise VectorStoreRequestError("temporary test failure")
        self.records.extend(records)

    async def delete_by_document(self, document_id: UUID) -> None:
        assert self._state.active == 0
        self.deleted_documents.append(document_id)
        self.records = [record for record in self.records if record.document_id != document_id]

    async def delete_by_chunk_ids(self, chunk_ids: Sequence[UUID]) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


class _Repositories:
    def __init__(self, job: IngestionJob) -> None:
        self.job = job
        self.claim_enabled = True
        self.owned = True
        self.expired: list[IngestionJob] = []
        self.replaced_chunks: list[DocumentChunk] = []
        self.chunks_by_document: dict[UUID, list[DocumentChunk]] = {}
        self.documents: dict[UUID, Document] = {job.document.id: job.document}
        self.knowledge_base: KnowledgeBase | None = None
        self.knowledge_base_documents: list[Document] = []
        self.renewed = asyncio.Event()

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        harness = self

        async def lock_expired(
            repository: IngestionJobRepository,
            *,
            now: datetime,
            limit: int,
        ) -> list[IngestionJob]:
            return harness.expired[:limit]

        async def claim_next(
            repository: IngestionJobRepository,
            *,
            worker_id: str,
            claimed_at: datetime,
            lease_expires_at: datetime,
        ) -> IngestionJob | None:
            if not harness.claim_enabled:
                return None
            harness.claim_enabled = False
            job = harness.job
            job.status = IngestionJobStatus.PROCESSING.value
            job.document.status = DocumentStatus.PROCESSING.value
            job.attempt_count += 1
            job.claimed_by = worker_id
            job.claimed_at = claimed_at
            job.lease_expires_at = lease_expires_at
            job.started_at = claimed_at
            return job

        async def get_owned(
            repository: IngestionJobRepository,
            job_id: UUID,
            *,
            worker_id: str,
            now: datetime,
            for_update: bool = False,
        ) -> IngestionJob | None:
            if not harness.owned or harness.job.id != job_id or harness.job.claimed_by != worker_id:
                return None
            if harness.job.lease_expires_at is not None:
                harness.renewed.set()
            return harness.job

        async def replace_chunks(
            repository: DocumentChunkRepository,
            document_id: UUID,
            chunks: Sequence[DocumentChunk],
        ) -> None:
            harness.replaced_chunks = list(chunks)
            harness.chunks_by_document[document_id] = list(chunks)

        async def get_document(
            repository: DocumentRepository,
            document_id: UUID,
        ) -> Document | None:
            return harness.documents.get(document_id)

        async def list_chunks(
            repository: DocumentChunkRepository,
            document_id: UUID,
            *,
            limit: int | None = None,
        ) -> list[DocumentChunk]:
            chunks = harness.chunks_by_document.get(document_id, [])
            return chunks if limit is None else chunks[:limit]

        async def get_knowledge_base(
            repository: KnowledgeBaseRepository,
            knowledge_base_id: UUID,
        ) -> KnowledgeBase | None:
            if (
                harness.knowledge_base is not None
                and harness.knowledge_base.id == knowledge_base_id
            ):
                return harness.knowledge_base
            return None

        async def list_documents(
            repository: DocumentRepository,
            knowledge_base_id: UUID,
            *,
            limit: int,
            offset: int,
        ) -> list[Document]:
            return harness.knowledge_base_documents[offset : offset + limit]

        monkeypatch.setattr(
            IngestionJobRepository,
            "lock_expired_leases_internal",
            lock_expired,
        )
        monkeypatch.setattr(
            IngestionJobRepository,
            "claim_next_internal",
            claim_next,
        )
        monkeypatch.setattr(
            IngestionJobRepository,
            "get_owned_processing_internal",
            get_owned,
        )
        monkeypatch.setattr(
            DocumentChunkRepository,
            "replace_for_document_internal",
            replace_chunks,
        )
        monkeypatch.setattr(
            DocumentChunkRepository,
            "list_for_document_internal",
            list_chunks,
        )
        monkeypatch.setattr(DocumentRepository, "get_internal", get_document)
        monkeypatch.setattr(
            DocumentRepository,
            "list_for_knowledge_base_internal",
            list_documents,
        )
        monkeypatch.setattr(
            KnowledgeBaseRepository,
            "get_internal",
            get_knowledge_base,
        )


def _records(content: bytes, *, max_attempts: int = 3) -> tuple[Document, IngestionJob]:
    document = Document(
        id=uuid4(),
        knowledge_base_id=uuid4(),
        original_filename="notes.txt",
        media_type="text/plain",
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        storage_key="knowledge/document.txt",
        status=DocumentStatus.PENDING.value,
    )
    job = IngestionJob(
        id=uuid4(),
        document=document,
        status=IngestionJobStatus.PENDING.value,
        attempt_count=0,
        max_attempts=max_attempts,
        progress_percent=0,
    )
    return document, job


def _session_factory(state: _TransactionState) -> SessionFactory:
    return cast(SessionFactory, lambda: _Session(state))


def _service(
    *,
    state: _TransactionState,
    storage: _Storage,
    parser_registry: DocumentParserRegistry | None = None,
    embedding: _Embedding | None = None,
    vector_store: _VectorStore | None = None,
    lease_duration: timedelta = timedelta(minutes=5),
    rebuild_batch_size: int = 2,
) -> IngestionProcessingService:
    return IngestionProcessingService(
        session_factory=_session_factory(state),
        storage=storage,
        parser_registry=parser_registry or create_default_parser_registry(),
        normalizer=TextNormalizer(),
        chunker=DeterministicChunker(ChunkingConfig(chunk_size=18, overlap=4)),
        embedding_model=embedding or _Embedding(state),
        vector_store=vector_store or _VectorStore(state),
        worker_id="worker-test",
        lease_duration=lease_duration,
        retry_delay=timedelta(seconds=30),
        source_max_bytes=1024,
        rebuild_batch_size=rebuild_batch_size,
        clock=lambda: _NOW,
    )


def _durable_chunk(document_id: UUID, index: int, text: str) -> DocumentChunk:
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    return DocumentChunk(
        id=uuid5(document_id, f"{index}:{content_hash}"),
        document_id=document_id,
        chunk_index=index,
        normalized_text=text,
        token_count=len(text.split()),
        content_sha256=content_hash,
        start_offset=index * 10,
        end_offset=index * 10 + len(text),
    )


async def test_success_persists_stable_chunks_and_indexes_outside_transactions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"Alpha beta gamma. Delta epsilon zeta."
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
    )

    assert await service.process_next()

    assert state.active == 0
    assert state.sessions_opened == 4
    assert job.status == IngestionJobStatus.COMPLETED.value
    assert document.status == DocumentStatus.COMPLETED.value
    assert job.progress_percent == 100
    assert job.claimed_by is None
    assert job.lease_expires_at is None
    assert repositories.replaced_chunks
    for chunk in repositories.replaced_chunks:
        assert chunk.id == uuid5(
            document.id,
            f"{chunk.chunk_index}:{chunk.content_sha256}",
        )
        assert chunk.start_offset is not None
        assert chunk.end_offset is not None
    assert vector_store.deleted_documents == [document.id]
    assert len(vector_store.records) == len(repositories.replaced_chunks)


async def test_reprocessing_is_idempotent_until_content_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    storage = _Storage(content, state)
    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=storage,
        vector_store=vector_store,
    )

    assert await service.process_next()
    first_ids = [chunk.id for chunk in repositories.replaced_chunks]
    first_vector_ids = {
        record.vector_id for record in vector_store.records if record.document_id == document.id
    }
    assert len(first_ids) > 1

    unrelated_document_id = uuid4()
    unrelated_chunk = _durable_chunk(unrelated_document_id, 0, "unrelated")
    unrelated_record = VectorRecord(
        vector_id=stable_vector_id(unrelated_chunk.id),
        embedding=(7.0, 8.0),
        knowledge_base_id=uuid4(),
        document_id=unrelated_document_id,
        chunk_id=unrelated_chunk.id,
        chunk_index=unrelated_chunk.chunk_index,
        normalized_text=unrelated_chunk.normalized_text,
        content_hash=cast(str, unrelated_chunk.content_sha256),
    )
    vector_store.records.append(unrelated_record)

    job.status = IngestionJobStatus.PENDING.value
    document.status = DocumentStatus.PENDING.value
    repositories.claim_enabled = True

    assert await service.process_next()
    assert [chunk.id for chunk in repositories.replaced_chunks] == first_ids
    assert {
        record.vector_id for record in vector_store.records if record.document_id == document.id
    } == first_vector_ids
    assert unrelated_record in vector_store.records

    changed = b"Short replacement."
    storage.replace_content(changed)
    document.size_bytes = len(changed)
    document.sha256 = hashlib.sha256(changed).hexdigest()
    job.status = IngestionJobStatus.PENDING.value
    document.status = DocumentStatus.PENDING.value
    repositories.claim_enabled = True

    assert await service.process_next()
    replacement_ids = [chunk.id for chunk in repositories.replaced_chunks]
    replacement_vector_ids = {
        record.vector_id for record in vector_store.records if record.document_id == document.id
    }

    assert len(replacement_ids) == 1
    assert replacement_ids != first_ids
    assert replacement_vector_ids == {stable_vector_id(replacement_ids[0])}
    assert first_vector_ids.isdisjoint(replacement_vector_ids)
    assert unrelated_record in vector_store.records


async def test_real_task_cancellation_requeues_and_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"cancellation test text"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    read_started = asyncio.Event()
    release_read = asyncio.Event()
    read_finished = asyncio.Event()
    service = _service(
        state=state,
        storage=_Storage(
            content,
            state,
            started=read_started,
            release=release_read,
            finished=read_finished,
        ),
    )

    processing = asyncio.create_task(service.process_next())
    await read_started.wait()
    assert state.active == 0
    processing.cancel()

    with pytest.raises(asyncio.CancelledError):
        await processing

    assert read_finished.is_set()
    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "PROCESSING_CANCELLED"
    assert job.claimed_by is None
    assert job.lease_expires_at is None
    assert job.next_retry_at == _NOW + timedelta(seconds=30)


async def test_parser_thread_cancellation_propagates_without_downstream_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"parser cancellation"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    parser_started = asyncio.Event()
    parser_finished = asyncio.Event()
    release_parser = threading.Event()
    loop = asyncio.get_running_loop()

    class BlockingParser:
        supported_media_types = frozenset({"text/plain"})
        supported_extensions = frozenset({".txt"})

        def parse(self, parser_content: bytes) -> ParsedDocument:
            assert parser_content == content
            loop.call_soon_threadsafe(parser_started.set)
            try:
                release_parser.wait()
            finally:
                loop.call_soon_threadsafe(parser_finished.set)
            return ParsedDocument(sections=(ParsedSection(text="discarded result"),))

    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        parser_registry=DocumentParserRegistry((BlockingParser(),)),
        vector_store=vector_store,
    )

    processing = asyncio.create_task(service.process_next())
    await parser_started.wait()
    processing.cancel()
    try:
        with pytest.raises(asyncio.CancelledError):
            async with asyncio.timeout(1):
                await processing
    finally:
        release_parser.set()
        async with asyncio.timeout(1):
            await parser_finished.wait()

    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "PROCESSING_CANCELLED"
    assert repositories.replaced_chunks == []
    assert vector_store.deleted_documents == []
    assert vector_store.records == []


async def test_embedding_cancellation_requeues_without_vector_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"embedding cancellation"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    embedding_started = asyncio.Event()
    embedding_cancelled = asyncio.Event()

    class BlockingEmbedding(_Embedding):
        async def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
            assert self._state.active == 0
            assert texts
            embedding_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                embedding_cancelled.set()
                raise

    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        embedding=BlockingEmbedding(state),
        vector_store=vector_store,
    )

    processing = asyncio.create_task(service.process_next())
    await embedding_started.wait()
    processing.cancel()

    with pytest.raises(asyncio.CancelledError):
        await processing

    assert embedding_cancelled.is_set()
    assert repositories.replaced_chunks
    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "PROCESSING_CANCELLED"
    assert vector_store.deleted_documents == []
    assert vector_store.records == []


async def test_vector_index_cancellation_requeues_without_success_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"vector cancellation"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    upsert_started = asyncio.Event()
    upsert_cancelled = asyncio.Event()

    class BlockingVectorStore(_VectorStore):
        async def upsert(self, records: Sequence[VectorRecord]) -> None:
            assert self._state.active == 0
            assert records
            upsert_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                upsert_cancelled.set()
                raise

    vector_store = BlockingVectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
    )

    processing = asyncio.create_task(service.process_next())
    await upsert_started.wait()
    processing.cancel()

    with pytest.raises(asyncio.CancelledError):
        await processing

    assert upsert_cancelled.is_set()
    assert repositories.replaced_chunks
    assert vector_store.deleted_documents == [document.id]
    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "PROCESSING_CANCELLED"
    assert job.claimed_by is None


async def test_cancellation_propagates_when_requeue_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"cancellation cleanup failure"
    _, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    read_started = asyncio.Event()
    service = _service(
        state=state,
        storage=_Storage(
            content,
            state,
            started=read_started,
            release=asyncio.Event(),
        ),
    )

    async def fail_requeue(*_: object, **__: object) -> None:
        raise SQLAlchemyError("synthetic cleanup failure")

    monkeypatch.setattr(service, "_complete_failure", fail_requeue)
    processing = asyncio.create_task(service.process_next())
    await read_started.wait()
    processing.cancel()

    with pytest.raises(asyncio.CancelledError) as exc_info:
        await processing

    assert any(
        "lease-expiry recovery is required" in note
        for note in getattr(exc_info.value, "__notes__", ())
    )
    assert job.status == IngestionJobStatus.PROCESSING.value
    assert job.claimed_by == "worker-test"


async def test_deterministic_parser_failure_is_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"\xff\xfeinvalid utf8"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    service = _service(state=state, storage=_Storage(content, state))

    assert await service.process_next()

    assert job.status == IngestionJobStatus.FAILED.value
    assert document.status == DocumentStatus.FAILED.value
    assert job.error_code == "DOCUMENT_PROCESSING_FAILED"
    assert job.next_retry_at is None


async def test_transient_vector_failure_schedules_retry_after_atomic_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"retryable vector dependency failure"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    vector_store = _VectorStore(state, fail_on_upsert=1)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
    )

    assert await service.process_next()

    assert repositories.replaced_chunks
    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "INGESTION_DEPENDENCY_FAILED"
    assert job.next_retry_at == _NOW + timedelta(seconds=30)


async def test_retry_replaces_a_partially_written_vector_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    vector_store = _VectorStore(state, fail_on_upsert=2)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
        rebuild_batch_size=1,
    )

    assert await service.process_next()

    partial_ids = {record.vector_id for record in vector_store.records}
    assert len(repositories.replaced_chunks) > 2
    assert len(partial_ids) == 1
    assert job.status == IngestionJobStatus.PENDING.value

    repositories.claim_enabled = True
    assert await service.process_next()

    final_ids = {record.vector_id for record in vector_store.records}
    expected_ids = {stable_vector_id(chunk.id) for chunk in repositories.replaced_chunks}
    assert job.status == IngestionJobStatus.COMPLETED.value
    assert document.status == DocumentStatus.COMPLETED.value
    assert final_ids == expected_ids
    assert len(vector_store.records) == len(expected_ids)
    assert partial_ids <= final_ids
    assert vector_store.deleted_documents == [document.id, document.id]


@pytest.mark.parametrize(
    ("max_attempts", "expected_status"),
    [
        (1, IngestionJobStatus.FAILED.value),
        (2, IngestionJobStatus.PENDING.value),
    ],
)
async def test_embedding_request_failure_retries_until_attempts_are_exhausted(
    monkeypatch: pytest.MonkeyPatch,
    max_attempts: int,
    expected_status: str,
) -> None:
    content = b"embedding request failure"
    document, job = _records(content, max_attempts=max_attempts)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    embedding = _Embedding(
        state,
        error=EmbeddingRequestError("provider unavailable"),
    )
    service = _service(
        state=state,
        storage=_Storage(content, state),
        embedding=embedding,
    )

    assert await service.process_next()

    assert job.attempt_count == 1
    assert job.status == expected_status
    assert document.status == expected_status
    assert job.error_code == "INGESTION_DEPENDENCY_FAILED"
    if expected_status == IngestionJobStatus.FAILED.value:
        assert job.next_retry_at is None
    else:
        assert job.next_retry_at == _NOW + timedelta(seconds=30)


async def test_source_integrity_failure_is_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authoritative = b"authoritative"
    stored = b"tampered-data"
    assert len(authoritative) == len(stored)
    document, job = _records(authoritative)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    service = _service(state=state, storage=_Storage(stored, state))

    assert await service.process_next()

    assert job.status == IngestionJobStatus.FAILED.value
    assert document.status == DocumentStatus.FAILED.value
    assert job.error_code == "SOURCE_INTEGRITY_FAILED"


async def test_lost_lease_prevents_persistence_and_external_index_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"lease loss"
    _, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.owned = False
    repositories.install(monkeypatch)
    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
    )

    assert await service.process_next()

    assert job.status == IngestionJobStatus.PROCESSING.value
    assert repositories.replaced_chunks == []
    assert vector_store.deleted_documents == []
    assert vector_store.records == []


async def test_unexpected_error_is_recorded_then_propagated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"unexpected failure"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    service = _service(
        state=state,
        storage=_Storage(content, state, error=RuntimeError("programmer bug")),
    )

    with pytest.raises(RuntimeError, match="programmer bug"):
        await service.process_next()

    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "INGESTION_FAILED"


async def test_heartbeat_renews_while_slow_stage_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"heartbeat test"
    _, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    read_started = asyncio.Event()
    release_read = asyncio.Event()
    service = _service(
        state=state,
        storage=_Storage(
            content,
            state,
            started=read_started,
            release=release_read,
        ),
        lease_duration=timedelta(milliseconds=30),
    )

    processing = asyncio.create_task(service.process_next())
    await read_started.wait()
    await repositories.renewed.wait()
    release_read.set()

    assert await processing
    assert job.status == IngestionJobStatus.COMPLETED.value


async def test_cancellation_cancels_a_blocked_heartbeat_and_requeues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"blocked heartbeat cancellation"
    document, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    read_started = asyncio.Event()
    renewal_started = asyncio.Event()
    renewal_cancelled = asyncio.Event()

    async def block_first_owned_lookup(
        repository: IngestionJobRepository,
        job_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        for_update: bool = False,
    ) -> IngestionJob | None:
        assert repository
        assert job_id == job.id
        assert worker_id == "worker-test"
        assert for_update
        if not renewal_started.is_set():
            renewal_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                renewal_cancelled.set()
                raise
        return job

    monkeypatch.setattr(
        IngestionJobRepository,
        "get_owned_processing_internal",
        block_first_owned_lookup,
    )
    service = _service(
        state=state,
        storage=_Storage(
            content,
            state,
            started=read_started,
            release=asyncio.Event(),
        ),
        lease_duration=timedelta(milliseconds=30),
    )

    processing = asyncio.create_task(service.process_next())
    await read_started.wait()
    await renewal_started.wait()
    processing.cancel()

    with pytest.raises(asyncio.CancelledError):
        async with asyncio.timeout(1):
            await processing

    assert renewal_cancelled.is_set()
    assert state.active == 0
    assert job.status == IngestionJobStatus.PENDING.value
    assert document.status == DocumentStatus.PENDING.value
    assert job.error_code == "PROCESSING_CANCELLED"
    assert job.claimed_by is None
    assert job.lease_expires_at is None


async def test_expired_recovery_requeues_or_terminally_fails_within_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"recovery"
    _, job = _records(content)
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    retry_document, retry_job = _records(content)
    retry_job.status = IngestionJobStatus.PROCESSING.value
    retry_document.status = DocumentStatus.PROCESSING.value
    retry_job.attempt_count = 1
    retry_job.claimed_by = "dead-worker"
    retry_job.claimed_at = _NOW - timedelta(minutes=10)
    retry_job.lease_expires_at = _NOW - timedelta(minutes=5)
    failed_document, failed_job = _records(content, max_attempts=1)
    failed_job.status = IngestionJobStatus.PROCESSING.value
    failed_document.status = DocumentStatus.PROCESSING.value
    failed_job.attempt_count = 1
    failed_job.claimed_by = "dead-worker"
    failed_job.claimed_at = _NOW - timedelta(minutes=10)
    failed_job.lease_expires_at = _NOW - timedelta(minutes=5)
    repositories.expired = [retry_job, failed_job]
    service = _service(state=state, storage=_Storage(content, state))

    assert await service.recover_expired_leases(limit=2) == 2

    assert retry_job.status == IngestionJobStatus.PENDING.value
    assert retry_job.next_retry_at == _NOW + timedelta(seconds=30)
    assert retry_job.claimed_by is None
    assert failed_job.status == IngestionJobStatus.FAILED.value
    assert failed_document.status == DocumentStatus.FAILED.value
    assert failed_job.finished_at == _NOW


async def test_document_rebuild_reports_partial_provider_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"rebuild"
    document, job = _records(content)
    document.status = DocumentStatus.COMPLETED.value
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    repositories.chunks_by_document[document.id] = [
        _durable_chunk(document.id, 0, "first"),
        _durable_chunk(document.id, 1, "second"),
    ]
    vector_store = _VectorStore(state, fail_on_upsert=2)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
        rebuild_batch_size=1,
    )

    result = await service.rebuild_document(document.id, max_chunks=2)

    assert result.documents_seen == 1
    assert result.documents_indexed == 0
    assert result.chunks_indexed == 1
    assert len(result.failures) == 1
    assert result.failures[0].document_id == document.id
    assert result.failures[0].code == "INGESTION_DEPENDENCY_FAILED"


@pytest.mark.parametrize(
    "status",
    [DocumentStatus.PENDING.value, DocumentStatus.PROCESSING.value, DocumentStatus.FAILED.value],
)
async def test_knowledge_base_rebuild_does_not_delete_noncompleted_document_vectors(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    content = b"noncompleted rebuild"
    document, job = _records(content)
    document.status = status
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    repositories.knowledge_base = KnowledgeBase(
        id=document.knowledge_base_id,
        name="Knowledge",
    )
    repositories.knowledge_base_documents = [document]
    durable_chunk = _durable_chunk(document.id, 0, "authoritative")
    existing_record = VectorRecord(
        vector_id=stable_vector_id(durable_chunk.id),
        embedding=(1.0, 2.0),
        knowledge_base_id=document.knowledge_base_id,
        document_id=document.id,
        chunk_id=durable_chunk.id,
        chunk_index=durable_chunk.chunk_index,
        normalized_text=durable_chunk.normalized_text,
        content_hash=cast(str, durable_chunk.content_sha256),
    )
    vector_store = _VectorStore(state)
    vector_store.records.append(existing_record)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
    )

    result = await service.rebuild_knowledge_base(
        document.knowledge_base_id,
        max_documents=1,
        max_chunks_per_document=1,
    )

    assert result.documents_seen == 1
    assert result.documents_indexed == 0
    assert result.chunks_indexed == 0
    assert len(result.failures) == 1
    assert result.failures[0].document_id == document.id
    assert result.failures[0].code == "REBUILD_NOT_READY"
    assert vector_store.deleted_documents == []
    assert vector_store.records == [existing_record]


async def test_knowledge_base_rebuild_aggregates_per_document_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = b"knowledge rebuild"
    first, job = _records(content)
    second, _ = _records(content)
    first.status = DocumentStatus.COMPLETED.value
    second.status = DocumentStatus.COMPLETED.value
    second.knowledge_base_id = first.knowledge_base_id
    state = _TransactionState()
    repositories = _Repositories(job)
    repositories.install(monkeypatch)
    repositories.documents = {first.id: first, second.id: second}
    repositories.knowledge_base = KnowledgeBase(
        id=first.knowledge_base_id,
        name="Knowledge",
    )
    repositories.knowledge_base_documents = [first, second]
    repositories.chunks_by_document = {
        first.id: [_durable_chunk(first.id, 0, "first")],
        second.id: [_durable_chunk(second.id, 0, "second")],
    }
    vector_store = _VectorStore(state, fail_on_upsert=2)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        vector_store=vector_store,
        rebuild_batch_size=1,
    )

    result = await service.rebuild_knowledge_base(
        first.knowledge_base_id,
        max_documents=2,
        max_chunks_per_document=1,
    )

    assert result.documents_seen == 2
    assert result.documents_indexed == 1
    assert result.chunks_indexed == 1
    assert [failure.document_id for failure in result.failures] == [second.id]


async def test_close_closes_vector_store_even_when_embedding_close_fails() -> None:
    content = b"close"
    state = _TransactionState()
    embedding = _Embedding(
        state,
        close_error=RuntimeError("embedding close failed"),
    )
    vector_store = _VectorStore(state)
    service = _service(
        state=state,
        storage=_Storage(content, state),
        embedding=embedding,
        vector_store=vector_store,
    )

    with pytest.raises(RuntimeError, match="embedding close failed"):
        await service.close()

    assert embedding.closed
    assert vector_store.closed
