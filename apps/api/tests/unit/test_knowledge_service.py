"""AF-1 service behavior, deduplication, cleanup, and retry tests."""

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api.errors import (
    ConflictError,
    InvalidUploadError,
    NotFoundError,
    ServiceUnavailableError,
    UnsupportedMediaTypeError,
    UploadTooLargeError,
)
from app.db.models import Document, IngestionJob, KnowledgeBase
from app.ingestion.storage import LocalFileStorage
from app.services.knowledge_intake import KnowledgeIntakeService


class MemoryStream:
    """Async byte stream used by service tests."""

    def __init__(self, content: bytes) -> None:
        self._content = content
        self._read = False

    async def read(self, size: int = -1) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._content if size != 0 else b""


def _matches(path: Path, pattern: str) -> list[Path]:
    return list(path.rglob(pattern))


class TransactionContext(AbstractAsyncContextManager[None]):
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.flush = AsyncMock()

    def begin(self) -> TransactionContext:
        return TransactionContext()


def _timestamp_records() -> tuple[KnowledgeBase, Document, IngestionJob]:
    now = datetime.now(UTC)
    knowledge_base = KnowledgeBase(id=uuid4(), name="Engineering", created_at=now, updated_at=now)
    document = Document(
        id=uuid4(),
        knowledge_base_id=knowledge_base.id,
        original_filename="notes.txt",
        media_type="text/plain",
        size_bytes=5,
        sha256="a" * 64,
        storage_key=f"{knowledge_base.id}/{uuid4()}.txt",
        status="failed",
        created_at=now,
        updated_at=now,
    )
    job = IngestionJob(
        id=uuid4(),
        document=document,
        document_id=document.id,
        status="failed",
        attempt_count=1,
        error_code="PARSER_FAILED",
        safe_error_message="The document could not be processed.",
        started_at=now,
        finished_at=now,
        created_at=now,
        updated_at=now,
    )
    document.ingestion_job = job
    return knowledge_base, document, job


def _service(tmp_path: Path) -> KnowledgeIntakeService:
    service = KnowledgeIntakeService(
        FakeSession(),  # type: ignore[arg-type]
        LocalFileStorage(tmp_path),
        max_upload_size_bytes=1024,
    )
    service._knowledge_bases = AsyncMock()  # type: ignore[assignment]
    service._documents = AsyncMock()  # type: ignore[assignment]
    service._jobs = AsyncMock()  # type: ignore[assignment]
    return service


async def test_upload_creates_document_and_single_durable_job(tmp_path: Path) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._documents.get_by_digest.return_value = None  # type: ignore[attr-defined]

    result = await service.upload_document(
        knowledge_base.id,
        filename="notes.txt",
        media_type="text/plain",
        source=MemoryStream(b"hello"),
    )

    assert result.duplicate is False
    assert result.document.sha256 == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )
    assert result.document.status == "pending"
    assert result.job.status == "pending"
    assert result.job.attempt_count == 0
    service._documents.add.assert_awaited_once_with(result.document)  # type: ignore[attr-defined]
    service._jobs.add.assert_awaited_once_with(result.job)  # type: ignore[attr-defined]
    assert (tmp_path / result.document.storage_key).read_bytes() == b"hello"


@pytest.mark.parametrize(
    ("filename", "media_type", "content"),
    [
        ("document.pdf", "application/pdf", b"%PDF-1.7\nminimal"),
        ("notes.md", "text/markdown", b"# Notes\n"),
    ],
)
async def test_supported_pdf_and_markdown_reach_durable_pending_state(
    tmp_path: Path,
    filename: str,
    media_type: str,
    content: bytes,
) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._documents.get_by_digest.return_value = None  # type: ignore[attr-defined]

    result = await service.upload_document(
        knowledge_base.id,
        filename=filename,
        media_type=media_type,
        source=MemoryStream(content),
    )

    assert result.document.original_filename == filename
    assert result.document.media_type == media_type
    assert result.document.status == "pending"
    assert (tmp_path / result.document.storage_key).read_bytes() == content


async def test_duplicate_upload_returns_existing_resources_and_removes_new_file(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    knowledge_base, document, job = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._documents.get_by_digest.return_value = document  # type: ignore[attr-defined]

    result = await service.upload_document(
        knowledge_base.id,
        filename="copy.txt",
        media_type="text/plain",
        source=MemoryStream(b"hello"),
    )

    assert result == result.__class__(document, job, duplicate=True)
    assert not _matches(tmp_path, "*.txt")
    service._documents.add.assert_not_awaited()  # type: ignore[attr-defined]


async def test_simulated_concurrent_uniqueness_conflict_returns_existing(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    knowledge_base, document, job = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._documents.get_by_digest.side_effect = [None, document]  # type: ignore[attr-defined]
    service._documents.add.side_effect = IntegrityError("insert", {}, Exception())  # type: ignore[attr-defined]

    result = await service.upload_document(
        knowledge_base.id,
        filename="copy.txt",
        media_type="text/plain",
        source=MemoryStream(b"hello"),
    )

    assert result.document is document
    assert result.job is job
    assert result.duplicate is True
    assert not _matches(tmp_path, "*.txt")


async def test_database_failure_removes_stored_file_and_hides_internal_error(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._documents.get_by_digest.return_value = None  # type: ignore[attr-defined]
    service._documents.add.side_effect = OperationalError(  # type: ignore[attr-defined]
        "INSERT PRIVATE PATH",
        {},
        Exception("/private/secret/path"),
    )

    with pytest.raises(ServiceUnavailableError) as exc_info:
        await service.upload_document(
            knowledge_base.id,
            filename="notes.txt",
            media_type="text/plain",
            source=MemoryStream(b"hello"),
        )

    assert exc_info.value.public_message == "Database is temporarily unavailable."
    assert "/private/secret/path" not in exc_info.value.public_message
    assert not _matches(tmp_path, "*.txt")


async def test_invalid_pdf_signature_cleans_stored_file(tmp_path: Path) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]

    with pytest.raises(InvalidUploadError, match="signature"):
        await service.upload_document(
            knowledge_base.id,
            filename="document.pdf",
            media_type="application/pdf",
            source=MemoryStream(b"not a pdf"),
        )

    assert not _matches(tmp_path, "*.pdf")


async def test_unknown_knowledge_base_writes_no_file(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service._knowledge_bases.get.return_value = None  # type: ignore[attr-defined]

    with pytest.raises(NotFoundError):
        await service.upload_document(
            uuid4(),
            filename="notes.txt",
            media_type="text/plain",
            source=MemoryStream(b"hello"),
        )

    assert not _matches(tmp_path, "*.*")


async def test_service_crud_queries_return_durable_records(tmp_path: Path) -> None:
    service = _service(tmp_path)
    knowledge_base, document, job = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]
    service._knowledge_bases.list.return_value = [knowledge_base]  # type: ignore[attr-defined]
    service._documents.get.return_value = document  # type: ignore[attr-defined]
    service._documents.list_for_knowledge_base.return_value = [document]  # type: ignore[attr-defined]
    service._jobs.get.return_value = job  # type: ignore[attr-defined]

    created = await service.create_knowledge_base(name="New", description=None)
    listed = await service.list_knowledge_bases(limit=10, offset=0)
    retrieved = await service.get_knowledge_base(knowledge_base.id)
    documents = await service.list_documents(knowledge_base.id, limit=10, offset=0)
    retrieved_document = await service.get_document(document.id)
    retrieved_job = await service.get_ingestion_job(job.id)

    assert created.name == "New"
    assert listed == [knowledge_base]
    assert retrieved is knowledge_base
    assert documents == [document]
    assert retrieved_document is document
    assert retrieved_job is job
    service._knowledge_bases.add.assert_awaited_once_with(created)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("filename", "media_type", "expected_exception"),
    [
        ("../unsafe.txt", "text/plain", InvalidUploadError),
        ("unsafe\\name.txt", "text/plain", InvalidUploadError),
        ("notes.exe", "application/octet-stream", UnsupportedMediaTypeError),
        ("notes.md", "text/plain", UnsupportedMediaTypeError),
    ],
)
async def test_upload_metadata_validation_rejects_unsafe_or_unsupported_input(
    tmp_path: Path,
    filename: str,
    media_type: str,
    expected_exception: type[Exception],
) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]

    with pytest.raises(expected_exception):
        await service.upload_document(
            knowledge_base.id,
            filename=filename,
            media_type=media_type,
            source=MemoryStream(b"content"),
        )

    assert not _matches(tmp_path, "*.*")


async def test_empty_and_oversized_uploads_map_to_safe_errors(tmp_path: Path) -> None:
    service = _service(tmp_path)
    knowledge_base, _, _ = _timestamp_records()
    service._knowledge_bases.get.return_value = knowledge_base  # type: ignore[attr-defined]

    with pytest.raises(InvalidUploadError, match="empty"):
        await service.upload_document(
            knowledge_base.id,
            filename="empty.txt",
            media_type="text/plain",
            source=MemoryStream(b""),
        )

    service._max_upload_size_bytes = 2
    with pytest.raises(UploadTooLargeError):
        await service.upload_document(
            knowledge_base.id,
            filename="large.txt",
            media_type="text/plain",
            source=MemoryStream(b"large"),
        )


async def test_failed_job_retry_reuses_row_and_resets_document() -> None:
    service = _service(Path("/unused"))
    _, document, job = _timestamp_records()
    service._jobs.get.return_value = job  # type: ignore[attr-defined]

    result = await service.retry_ingestion_job(job.id)

    assert result is job
    assert job.status == "pending"
    assert document.status == "pending"
    assert job.attempt_count == 1
    assert job.error_code is None
    assert job.safe_error_message is None
    assert job.started_at is None
    assert job.finished_at is None


async def test_retry_is_idempotent_when_job_is_already_pending() -> None:
    service = _service(Path("/unused"))
    _, _, job = _timestamp_records()
    job.status = "pending"
    service._jobs.get.return_value = job  # type: ignore[attr-defined]

    assert await service.retry_ingestion_job(job.id) is job
    service._session.flush.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize("job_status", ["processing", "completed"])
async def test_retry_rejects_invalid_state(job_status: str) -> None:
    service = _service(Path("/unused"))
    _, _, job = _timestamp_records()
    job.status = job_status
    service._jobs.get.return_value = job  # type: ignore[attr-defined]

    with pytest.raises(ConflictError, match="Only failed"):
        await service.retry_ingestion_job(job.id)
