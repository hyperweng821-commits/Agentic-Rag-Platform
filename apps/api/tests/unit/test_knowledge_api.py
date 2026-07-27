"""AF-1 knowledge-base and document API contract tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api.dependencies import get_knowledge_intake_service
from app.api.errors import (
    InvalidUploadError,
    NotFoundError,
    UnsupportedMediaTypeError,
    UploadTooLargeError,
)
from app.db.models import Document, IngestionJob, KnowledgeBase
from app.services.knowledge_intake import KnowledgeIntakeService, UploadResult


@pytest.fixture
def knowledge_service(application: FastAPI) -> AsyncMock:
    """Override AF-1 use cases without PostgreSQL or local storage."""
    service = AsyncMock(spec=KnowledgeIntakeService)
    application.dependency_overrides[get_knowledge_intake_service] = lambda: service
    return service


def _resources() -> tuple[KnowledgeBase, Document, IngestionJob]:
    now = datetime.now(UTC)
    knowledge_base = KnowledgeBase(
        id=uuid4(),
        name="Engineering",
        description="Private notes",
        created_at=now,
        updated_at=now,
    )
    document = Document(
        id=uuid4(),
        knowledge_base_id=knowledge_base.id,
        original_filename="notes.txt",
        media_type="text/plain",
        size_bytes=5,
        sha256="a" * 64,
        storage_key="private/host/path.txt",
        status="pending",
        created_at=now,
        updated_at=now,
    )
    job = IngestionJob(
        id=uuid4(),
        document_id=document.id,
        status="pending",
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    return knowledge_base, document, job


async def test_create_list_and_retrieve_knowledge_base_contracts(
    client: AsyncClient,
    knowledge_service: AsyncMock,
) -> None:
    knowledge_base, _, _ = _resources()
    knowledge_service.create_knowledge_base.return_value = knowledge_base
    knowledge_service.list_knowledge_bases.return_value = [knowledge_base]
    knowledge_service.get_knowledge_base.return_value = knowledge_base

    created = await client.post(
        "/api/v1/knowledge-bases",
        json={"name": " Engineering ", "description": " Private notes "},
    )
    listed = await client.get("/api/v1/knowledge-bases", params={"limit": 10, "offset": 0})
    retrieved = await client.get(f"/api/v1/knowledge-bases/{knowledge_base.id}")

    assert created.status_code == 201
    assert created.json()["name"] == "Engineering"
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == str(knowledge_base.id)
    assert listed.json()["limit"] == 10
    assert retrieved.status_code == 200
    knowledge_service.create_knowledge_base.assert_awaited_once_with(
        name="Engineering",
        description="Private notes",
    )


@pytest.mark.parametrize(
    ("filename", "media_type", "content"),
    [
        ("document.pdf", "application/pdf", b"%PDF-1.7\n"),
        ("notes.md", "text/markdown", b"# Notes\n"),
        ("notes.txt", "text/plain", b"Notes\n"),
    ],
)
async def test_supported_upload_contracts(
    client: AsyncClient,
    knowledge_service: AsyncMock,
    filename: str,
    media_type: str,
    content: bytes,
) -> None:
    knowledge_base, document, job = _resources()
    document.original_filename = filename
    document.media_type = media_type
    knowledge_service.upload_document.return_value = UploadResult(document, job, duplicate=False)

    response = await client.post(
        f"/api/v1/knowledge-bases/{knowledge_base.id}/documents",
        files={"file": (filename, content, media_type)},
    )

    assert response.status_code == 201
    assert response.json()["document"]["original_filename"] == filename
    assert response.json()["ingestion_job"]["status"] == "pending"
    assert response.json()["duplicate"] is False
    assert "storage_key" not in response.text
    assert "private/host/path" not in response.text


async def test_duplicate_upload_returns_existing_resource_with_200(
    client: AsyncClient,
    knowledge_service: AsyncMock,
) -> None:
    knowledge_base, document, job = _resources()
    knowledge_service.upload_document.return_value = UploadResult(document, job, duplicate=True)

    response = await client.post(
        f"/api/v1/knowledge-bases/{knowledge_base.id}/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["duplicate"] is True
    assert response.json()["document"]["id"] == str(document.id)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (UnsupportedMediaTypeError(), 415, "UNSUPPORTED_MEDIA_TYPE"),
        (InvalidUploadError("The uploaded file is empty."), 400, "INVALID_UPLOAD"),
        (UploadTooLargeError(), 413, "UPLOAD_TOO_LARGE"),
        (NotFoundError("Knowledge base was not found."), 404, "NOT_FOUND"),
    ],
)
async def test_upload_errors_use_safe_envelope(
    client: AsyncClient,
    knowledge_service: AsyncMock,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    knowledge_service.upload_document.side_effect = error

    response = await client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("file.exe", b"private contents", "application/octet-stream")},
    )

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    assert "private contents" not in response.text


async def test_malformed_identifier_uses_existing_validation_envelope(
    client: AsyncClient,
    knowledge_service: AsyncMock,
) -> None:
    response = await client.get("/api/v1/documents/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    knowledge_service.get_document.assert_not_awaited()


async def test_document_list_metadata_and_job_retry_contracts(
    client: AsyncClient,
    knowledge_service: AsyncMock,
) -> None:
    knowledge_base, document, job = _resources()
    knowledge_service.list_documents.return_value = [document]
    knowledge_service.get_document.return_value = document
    knowledge_service.get_ingestion_job.return_value = job
    knowledge_service.retry_ingestion_job.return_value = job

    listed = await client.get(f"/api/v1/knowledge-bases/{knowledge_base.id}/documents")
    retrieved = await client.get(f"/api/v1/documents/{document.id}")
    job_status = await client.get(f"/api/v1/ingestion-jobs/{job.id}")
    retried = await client.post(f"/api/v1/ingestion-jobs/{job.id}/retry")

    assert listed.status_code == 200
    assert retrieved.status_code == 200
    assert job_status.status_code == 200
    assert retried.status_code == 200
    assert retrieved.json()["sha256"] == "a" * 64
    assert retried.json()["id"] == str(job.id)
