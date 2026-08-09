"""Authenticated product Evidence API backed by existing Hybrid Retrieval."""

from collections.abc import Mapping
from typing import cast
from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CsrfProtectedAuthenticationProof, HybridRetrieval
from app.api.errors import (
    NotFoundError,
    RetrievalInvalidRequestError,
    RetrievalServiceUnavailableError,
)
from app.retrieval import (
    RetrievalAuthenticationError,
    RetrievalRequestValidationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
)
from app.retrieval.evidence import project_retrieved_evidence
from app.schemas.retrieval import (
    RetrievalEvidenceResponse,
    RetrievalQueryRequest,
    RetrievalResponse,
)
from app.security.authentication import AuthenticationError

router = APIRouter()


@router.post(
    "/knowledge-bases/{knowledge_base_id}/retrieval",
    response_model=RetrievalResponse,
    summary="Retrieve authoritative evidence",
)
async def retrieve_authoritative_evidence(
    knowledge_base_id: UUID,
    payload: RetrievalQueryRequest,
    proof: CsrfProtectedAuthenticationProof,
    service: HybridRetrieval,
) -> RetrievalResponse:
    """Retrieve and safely project evidence for one visible knowledge base."""
    try:
        result = await service.retrieve(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            payload=cast(Mapping[object, object], payload.model_dump()),
        )
        evidence = project_retrieved_evidence(result)
    except RetrievalRequestValidationError:
        raise RetrievalInvalidRequestError from None
    except RetrievalAuthenticationError:
        raise AuthenticationError from None
    except RetrievalTargetNotFoundError:
        raise NotFoundError from None
    except RetrievalUnavailableError:
        raise RetrievalServiceUnavailableError from None

    return RetrievalResponse(
        items=[RetrievalEvidenceResponse.model_validate(item) for item in evidence]
    )
