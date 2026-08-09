"""Focused HTTP contract tests for the authenticated product Evidence API."""

import hashlib
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.api import dependencies
from app.api.dependencies import (
    CsrfProtectedAuthenticationProof,
    get_authentication_service,
    get_hybrid_retrieval_service,
)
from app.core.config import Settings
from app.retrieval.domain import RetrievalRequestValidationError
from app.retrieval.hybrid import (
    HybridRetrievalResult,
    HybridRetrievalService,
    _FusedInternalAuthoritativeRetrievalRecord,
)
from app.retrieval.service import (
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    _InternalAuthoritativeRetrievalRecord,
    _TrustedAuthoritativeProvenance,
    _UntrustedDocumentContent,
)
from app.security import AuthenticationError, AuthenticationService, CsrfError, Principal
from app.security.authentication import SessionAuthenticationProof

SESSION_TOKEN = "s" * 43
CSRF_TOKEN = "c" * 43
PRIVATE_MARKERS = (
    "session_token",
    "csrf_token",
    "session_token_sha256",
    "proof",
    "provider_response",
    "rejected_candidate",
    "storage path",
)


def _proof() -> SessionAuthenticationProof:
    return SessionAuthenticationProof(
        principal=Principal(
            user_id=uuid4(),
            email="member@example.com",
            session_id=uuid4(),
        ),
        session_token_sha256="a" * 64,
    )


def _result() -> HybridRetrievalResult:
    content = "PostgreSQL-authoritative evidence"
    return HybridRetrievalResult(
        records=(
            _FusedInternalAuthoritativeRetrievalRecord(
                authoritative=_InternalAuthoritativeRetrievalRecord(
                    trusted=_TrustedAuthoritativeProvenance(
                        knowledge_base_id=uuid4(),
                        document_id=uuid4(),
                        chunk_id=uuid4(),
                        content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                        source_display_name="incident-runbook.md",
                        page_start=2,
                        page_end=3,
                        character_start=120,
                        character_end=120 + len(content),
                    ),
                    document_content=_UntrustedDocumentContent(text=content),
                ),
                keyword_rank=2,
                dense_rank=1,
                fused_numerator=123,
                fused_denominator=456,
                fused_rank=1,
            ),
        )
    )


@pytest.fixture
def authentication(application: FastAPI) -> AsyncMock:
    service = AsyncMock(spec=AuthenticationService)
    application.dependency_overrides[get_authentication_service] = lambda: service
    return service


@pytest.fixture
def retrieval_service(application: FastAPI) -> AsyncMock:
    service = AsyncMock(spec=HybridRetrievalService)

    async def override_service(
        proof: CsrfProtectedAuthenticationProof,
    ) -> AsyncIterator[HybridRetrievalService]:
        service.dependency_proof = proof
        yield service

    application.dependency_overrides[get_hybrid_retrieval_service] = override_service
    return service


def _authorize(
    client: AsyncClient,
    authentication: AsyncMock,
    *,
    proof: SessionAuthenticationProof | None = None,
) -> SessionAuthenticationProof:
    resolved = proof or _proof()
    authentication.authenticate_session_with_proof.return_value = resolved
    client.cookies.set("agentforge_session", SESSION_TOKEN, path="/api/v1")
    client.cookies.set("agentforge_csrf", CSRF_TOKEN, path="/")
    return resolved


def _assert_private_serialization(response_text: str) -> None:
    lowered = response_text.lower()
    for marker in PRIVATE_MARKERS:
        assert marker not in lowered


async def test_retrieval_success_returns_exact_evidence_envelope_and_reuses_proof(
    client: AsyncClient,
    authentication: AsyncMock,
    retrieval_service: AsyncMock,
) -> None:
    proof = _authorize(client, authentication)
    result = _result()
    retrieval_service.retrieve.return_value = result
    knowledge_base_id = uuid4()

    response = await client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/retrieval",
        headers={"X-CSRF-Token": CSRF_TOKEN},
        json={"query": "CI failure", "requested_count": 5},
    )

    source = result.records[0]
    trusted = source.authoritative.trusted
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "citation_id": str(trusted.chunk_id),
                "document_id": str(trusted.document_id),
                "source_display_name": trusted.source_display_name,
                "content": source.authoritative.document_content.text,
                "content_sha256": trusted.content_sha256,
                "page_start": 2,
                "page_end": 3,
                "character_start": 120,
                "character_end": 153,
                "trust_classification": "untrusted_document_content",
                "fused_rank": 1,
                "keyword_rank": 2,
                "dense_rank": 1,
            }
        ]
    }
    assert response.headers["cache-control"] == "private, no-store"
    authentication.authenticate_session_with_proof.assert_awaited_once_with(SESSION_TOKEN)
    authentication.validate_csrf.assert_awaited_once_with(
        session_token=SESSION_TOKEN,
        csrf_token=CSRF_TOKEN,
    )
    assert retrieval_service.dependency_proof is proof
    retrieval_service.retrieve.assert_awaited_once_with(
        proof=proof,
        knowledge_base_id=knowledge_base_id,
        payload={"query": "CI failure", "requested_count": 5},
    )
    _assert_private_serialization(response.text)


async def test_missing_session_stops_before_retrieval(
    client: AsyncClient,
    authentication: AsyncMock,
    retrieval_service: AsyncMock,
) -> None:
    authentication.authenticate_session_with_proof.side_effect = AuthenticationError

    response = await client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval",
        json={"query": "private query"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    retrieval_service.retrieve.assert_not_awaited()
    authentication.validate_csrf.assert_not_awaited()
    _assert_private_serialization(response.text)


@pytest.mark.parametrize("invalid_server_proof", [False, True], ids=["missing", "invalid"])
async def test_invalid_csrf_stops_before_retrieval(
    client: AsyncClient,
    authentication: AsyncMock,
    retrieval_service: AsyncMock,
    invalid_server_proof: bool,
) -> None:
    _authorize(client, authentication)
    headers: dict[str, str] = {}
    if invalid_server_proof:
        headers["X-CSRF-Token"] = CSRF_TOKEN
        authentication.validate_csrf.side_effect = CsrfError
    else:
        client.cookies.delete("agentforge_csrf", path="/")

    response = await client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval",
        headers=headers,
        json={"query": "private query"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    retrieval_service.retrieve.assert_not_awaited()
    _assert_private_serialization(response.text)


@pytest.mark.parametrize(
    ("failure", "status_code", "code", "message"),
    [
        (
            RetrievalAuthenticationError(),
            401,
            "AUTHENTICATION_REQUIRED",
            "Authentication is required.",
        ),
        (
            RetrievalTargetNotFoundError(),
            404,
            "NOT_FOUND",
            "The requested resource was not found.",
        ),
        (
            RetrievalRequestValidationError(),
            400,
            "RETRIEVAL_INVALID_REQUEST",
            "The retrieval request is invalid.",
        ),
        (
            RetrievalUnavailableError(),
            503,
            "RETRIEVAL_UNAVAILABLE",
            "Retrieval is temporarily unavailable.",
        ),
    ],
    ids=["stale-authentication", "hidden-target", "invalid-query", "unavailable"],
)
async def test_known_retrieval_failures_use_safe_public_errors(
    client: AsyncClient,
    authentication: AsyncMock,
    retrieval_service: AsyncMock,
    failure: Exception,
    status_code: int,
    code: str,
    message: str,
) -> None:
    _authorize(client, authentication)
    retrieval_service.retrieve.side_effect = failure

    response = await client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval",
        headers={"X-CSRF-Token": CSRF_TOKEN},
        json={"query": "   ", "requested_count": 10},
    )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["message"] == message
    assert "   " not in response.text
    assert response.headers["cache-control"] == "private, no-store"
    _assert_private_serialization(response.text)


async def test_missing_collection_configuration_is_safe_and_follows_authentication(
    application: FastAPI,
    client: AsyncClient,
    authentication: AsyncMock,
) -> None:
    _authorize(client, authentication)

    response = await client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval",
        headers={"X-CSRF-Token": CSRF_TOKEN},
        json={"query": "configuration boundary"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RETRIEVAL_UNAVAILABLE"
    assert response.json()["error"]["message"] == "Retrieval is temporarily unavailable."
    authentication.authenticate_session_with_proof.assert_awaited_once_with(SESSION_TOKEN)
    authentication.validate_csrf.assert_awaited_once()
    _assert_private_serialization(response.text)


async def test_hybrid_dependency_closes_both_adapters_and_propagates_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger: list[str] = []

    class FakeEmbedding:
        dimension = 4

        def __init__(self, **kwargs: object) -> None:
            ledger.append("embedding-created")

        async def close(self) -> None:
            ledger.append("embedding-closed")
            raise RuntimeError("cleanup failed")

    class FakeDense:
        def __init__(self, **kwargs: object) -> None:
            ledger.append("dense-created")

        async def close(self) -> None:
            ledger.append("dense-closed")

    monkeypatch.setattr(dependencies, "OllamaEmbeddingModel", FakeEmbedding)
    monkeypatch.setattr(dependencies, "ChromaDenseRetrievalAdapter", FakeDense)
    generator = dependencies.get_hybrid_retrieval_service(
        _proof(),
        Settings(_env_file=None, chroma_collection_uuid=uuid4()),
    )

    service = await anext(generator)

    assert isinstance(service, HybridRetrievalService)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        await generator.aclose()
    assert ledger == [
        "embedding-created",
        "dense-created",
        "embedding-closed",
        "dense-closed",
    ]


async def test_authorized_empty_still_executes_retrieval_and_returns_200(
    client: AsyncClient,
    authentication: AsyncMock,
    retrieval_service: AsyncMock,
) -> None:
    proof = _authorize(client, authentication)
    retrieval_service.retrieve.return_value = HybridRetrievalResult(records=())
    knowledge_base_id = uuid4()

    response = await client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/retrieval",
        headers={"X-CSRF-Token": CSRF_TOKEN},
        json={"query": "no matches"},
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}
    retrieval_service.retrieve.assert_awaited_once_with(
        proof=proof,
        knowledge_base_id=knowledge_base_id,
        payload={"query": "no matches", "requested_count": 10},
    )
    _assert_private_serialization(response.text)
