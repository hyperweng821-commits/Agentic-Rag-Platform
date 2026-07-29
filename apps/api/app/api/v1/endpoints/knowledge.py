"""Versioned AF-1 knowledge-base and document-intake endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.api.dependencies import CsrfProtectedPrincipal, CurrentPrincipal, KnowledgeService
from app.api.errors import UnsupportedMediaTypeError
from app.schemas.knowledge import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    IngestionJobResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
)

router = APIRouter()

PageLimit = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0, le=1_000_000)]


@router.post(
    "/knowledge-bases",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a knowledge base",
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    service: KnowledgeService,
    principal: CsrfProtectedPrincipal,
) -> KnowledgeBaseResponse:
    """Create one durable knowledge base."""
    knowledge_base = await service.create_knowledge_base(
        principal,
        name=payload.name,
        description=payload.description,
    )
    return KnowledgeBaseResponse.model_validate(knowledge_base)


@router.get(
    "/knowledge-bases",
    response_model=KnowledgeBaseListResponse,
    summary="List knowledge bases",
)
async def list_knowledge_bases(
    service: KnowledgeService,
    principal: CurrentPrincipal,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
) -> KnowledgeBaseListResponse:
    """List knowledge bases oldest-first with bounded offset pagination."""
    items = await service.list_knowledge_bases(principal, limit=limit, offset=offset)
    return KnowledgeBaseListResponse(
        items=[KnowledgeBaseResponse.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/knowledge-bases/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
    summary="Retrieve a knowledge base",
)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    service: KnowledgeService,
    principal: CurrentPrincipal,
) -> KnowledgeBaseResponse:
    """Retrieve one knowledge base by UUID."""
    return KnowledgeBaseResponse.model_validate(
        await service.get_knowledge_base(principal, knowledge_base_id)
    )


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    knowledge_base_id: UUID,
    service: KnowledgeService,
    principal: CsrfProtectedPrincipal,
    response: Response,
    file: Annotated[UploadFile, File(...)],
) -> DocumentUploadResponse:
    """Validate and stream one PDF, Markdown, or plain-text document."""
    if file.content_type is None:
        raise UnsupportedMediaTypeError()
    try:
        result = await service.upload_document(
            principal,
            knowledge_base_id,
            filename=file.filename or "",
            media_type=file.content_type,
            source=file,
        )
    finally:
        await file.close()

    if result.duplicate:
        response.status_code = status.HTTP_200_OK
    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(result.document),
        ingestion_job=IngestionJobResponse.model_validate(result.job),
        duplicate=result.duplicate,
    )


@router.get(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentListResponse,
    summary="List documents in a knowledge base",
)
async def list_documents(
    knowledge_base_id: UUID,
    service: KnowledgeService,
    principal: CurrentPrincipal,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
) -> DocumentListResponse:
    """List document metadata oldest-first with bounded pagination."""
    items = await service.list_documents(
        principal,
        knowledge_base_id,
        limit=limit,
        offset=offset,
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Retrieve document metadata",
)
async def get_document(
    document_id: UUID,
    service: KnowledgeService,
    principal: CurrentPrincipal,
) -> DocumentResponse:
    """Retrieve document metadata without exposing its host storage path."""
    return DocumentResponse.model_validate(await service.get_document(principal, document_id))


@router.get(
    "/ingestion-jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Retrieve ingestion-job status",
)
async def get_ingestion_job(
    job_id: UUID,
    service: KnowledgeService,
    principal: CurrentPrincipal,
) -> IngestionJobResponse:
    """Retrieve one durable job; AF-1 does not execute it."""
    return IngestionJobResponse.model_validate(await service.get_ingestion_job(principal, job_id))


@router.post(
    "/ingestion-jobs/{job_id}/retry",
    response_model=IngestionJobResponse,
    summary="Retry a failed ingestion job",
)
async def retry_ingestion_job(
    job_id: UUID,
    service: KnowledgeService,
    principal: CsrfProtectedPrincipal,
) -> IngestionJobResponse:
    """Idempotently requeue the same failed job record."""
    return IngestionJobResponse.model_validate(await service.retry_ingestion_job(principal, job_id))
