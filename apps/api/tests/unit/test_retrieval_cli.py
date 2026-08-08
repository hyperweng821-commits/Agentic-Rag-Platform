"""Tests for the authenticated non-HTTP AF-3B inspection command."""

import argparse
import hashlib
from uuid import uuid4

import pytest

from app.cli import retrieval
from app.core.config import Settings
from app.retrieval.domain import RetrievalRequestValidationError
from app.retrieval.hybrid import (
    HybridRetrievalResult,
    _FusedInternalAuthoritativeRetrievalRecord,
)
from app.retrieval.service import (
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    _InternalAuthoritativeRetrievalRecord,
    _TrustedAuthoritativeProvenance,
    _UntrustedDocumentContent,
)
from app.security.authentication import AuthenticationError, SessionAuthenticationProof
from app.security.principal import Principal

_SESSION_TOKEN = "private-session-token"  # noqa: S105


def _result() -> HybridRetrievalResult:
    knowledge_base_id = uuid4()
    document_id = uuid4()
    chunk_id = uuid4()
    content = "private-document-content"
    authoritative = _InternalAuthoritativeRetrievalRecord(
        trusted=_TrustedAuthoritativeProvenance(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            chunk_id=chunk_id,
            content_sha256=hashlib.sha256(content.encode()).hexdigest(),
            source_display_name="source\nname.txt",
            page_start=None,
            page_end=None,
            character_start=0,
            character_end=len(content),
        ),
        document_content=_UntrustedDocumentContent(text=content),
    )
    return HybridRetrievalResult(
        records=(
            _FusedInternalAuthoritativeRetrievalRecord(
                authoritative=authoritative,
                keyword_rank=2,
                dense_rank=1,
                fused_numerator=123,
                fused_denominator=456,
                fused_rank=1,
            ),
        ),
    )


def _proof() -> SessionAuthenticationProof:
    return SessionAuthenticationProof(
        principal=Principal(user_id=uuid4(), email="member@example.com", session_id=uuid4()),
        session_token_sha256="a" * 64,
    )


def test_inspection_main_prompts_for_private_inputs_and_prints_bounded_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = iter(("private-session-token", "private-query"))
    captured: dict[str, object] = {}
    expected = _result()

    async def fake_run(
        args: argparse.Namespace,
        *,
        session_token: str,
        query: str,
    ) -> HybridRetrievalResult:
        captured.update(
            {
                "knowledge_base_id": args.knowledge_base_id,
                "requested_count": args.requested_count,
                "session_token": session_token,
                "query": query,
            }
        )
        return expected

    monkeypatch.setattr("app.cli.retrieval.getpass.getpass", lambda prompt: next(inputs))
    monkeypatch.setattr(retrieval, "_run_and_dispose", fake_run)
    knowledge_base_id = uuid4()

    status = retrieval.main(
        ["inspect", "--knowledge-base-id", str(knowledge_base_id), "--requested-count", "3"]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert captured == {
        "knowledge_base_id": knowledge_base_id,
        "requested_count": 3,
        "session_token": "private-session-token",
        "query": "private-query",
    }
    assert "fused_rank=1" in output
    assert "keyword_rank=2" in output
    assert "dense_rank=1" in output
    trusted = expected.records[0].authoritative.trusted
    assert str(trusted.chunk_id) not in output
    assert str(trusted.document_id) not in output
    assert trusted.source_display_name not in output
    assert "chunk_id=" not in output
    assert "document_id=" not in output
    assert "source_display_name=" not in output
    assert "removed" not in output
    assert "private-session-token" not in output
    assert "private-query" not in output
    assert "private-document-content" not in output
    assert "source\\nname.txt" not in output


def test_inspection_main_normalizes_authentication_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = iter(("private-session-token", "private-query"))

    async def fail(
        args: argparse.Namespace,
        *,
        session_token: str,
        query: str,
    ) -> HybridRetrievalResult:
        raise AuthenticationError

    monkeypatch.setattr("app.cli.retrieval.getpass.getpass", lambda prompt: next(inputs))
    monkeypatch.setattr(retrieval, "_run_and_dispose", fail)

    status = retrieval.main(["inspect", "--knowledge-base-id", str(uuid4())])

    assert status == 2
    assert capsys.readouterr().out == "Error: authentication failed.\n"


async def test_authenticate_session_uses_real_proof_path_and_releases_limiter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proof = _proof()
    state: dict[str, object] = {}

    class FakeSessionContext:
        async def __aenter__(self) -> object:
            state["session_entered"] = True
            return object()

        async def __aexit__(self, *args: object) -> None:
            state["session_exited"] = True

    class FakeSessionMaker:
        def __call__(self) -> FakeSessionContext:
            return FakeSessionContext()

    class FakeLimiter:
        def __init__(self, max_concurrency: int) -> None:
            state["max_concurrency"] = max_concurrency

        def shutdown(self) -> None:
            state["limiter_shutdown"] = True

    class FakeAuthenticationService:
        def __init__(self, session: object, **kwargs: object) -> None:
            state["authentication_session"] = session
            state["authentication_options"] = kwargs

        async def authenticate_session_with_proof(
            self,
            session_token: str,
        ) -> SessionAuthenticationProof:
            state["session_token"] = session_token
            return proof

    monkeypatch.setattr(retrieval, "async_session_maker", FakeSessionMaker())
    monkeypatch.setattr(retrieval, "PasswordWorkLimiter", FakeLimiter)
    monkeypatch.setattr(retrieval, "AuthenticationService", FakeAuthenticationService)
    settings = Settings(_env_file=None, argon2_max_concurrency=3)

    observed = await retrieval._authenticate_session(
        settings=settings,
        session_token=_SESSION_TOKEN,
    )

    assert observed is proof
    assert state["session_entered"] is True
    assert state["session_exited"] is True
    assert state["limiter_shutdown"] is True
    assert state["max_concurrency"] == 3
    assert state["session_token"] == _SESSION_TOKEN


async def test_inspect_builds_real_adapters_around_authenticated_service_and_closes_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collection_uuid = uuid4()
    settings = Settings(
        _env_file=None,
        chroma_collection_uuid=collection_uuid,
        embedding_dimension=4,
    )
    proof = _proof()
    expected = _result()
    state: dict[str, object] = {}

    async def fake_authenticate(**kwargs: object) -> SessionAuthenticationProof:
        state["authentication"] = kwargs
        return proof

    class FakeHybridService:
        def __init__(self, **kwargs: object) -> None:
            state["service_options"] = kwargs

        async def retrieve(self, **kwargs: object) -> HybridRetrievalResult:
            state["retrieve"] = kwargs
            return expected

    monkeypatch.setattr(retrieval, "get_settings", lambda: settings)
    monkeypatch.setattr(retrieval, "_authenticate_session", fake_authenticate)
    monkeypatch.setattr(retrieval, "HybridRetrievalService", FakeHybridService)
    args = argparse.Namespace(knowledge_base_id=uuid4(), requested_count=7)

    observed = await retrieval._inspect(
        args,
        session_token=_SESSION_TOKEN,
        query="private-query",
    )

    assert observed is expected
    assert state["authentication"] == {
        "settings": settings,
        "session_token": "private-session-token",
    }
    assert state["retrieve"] == {
        "proof": proof,
        "knowledge_base_id": args.knowledge_base_id,
        "payload": {"query": "private-query", "requested_count": 7},
    }


async def test_inspect_requires_trusted_collection_uuid_before_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(retrieval, "get_settings", lambda: Settings(_env_file=None))

    with pytest.raises(retrieval.RetrievalInspectionError, match="CHROMA_COLLECTION_UUID"):
        await retrieval._inspect(
            argparse.Namespace(knowledge_base_id=uuid4(), requested_count=1),
            session_token=_SESSION_TOKEN,
            query="private-query",
        )


async def test_run_and_dispose_releases_engine_after_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _result()
    disposed = False

    async def fake_inspect(*args: object, **kwargs: object) -> HybridRetrievalResult:
        return expected

    async def fake_dispose() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr(retrieval, "_inspect", fake_inspect)
    monkeypatch.setattr(retrieval, "dispose_engine", fake_dispose)

    observed = await retrieval._run_and_dispose(
        argparse.Namespace(),
        session_token=_SESSION_TOKEN,
        query="private-query",
    )

    assert observed is expected
    assert disposed is True


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (RetrievalTargetNotFoundError(), "target was not found"),
        (RetrievalRequestValidationError(), "request validation failed"),
        (RetrievalUnavailableError(), "retrieval is unavailable"),
    ],
)
def test_inspection_main_normalizes_non_authentication_failures(
    error: Exception,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs = iter(("private-session-token", "private-query"))

    async def fail(
        args: argparse.Namespace,
        *,
        session_token: str,
        query: str,
    ) -> HybridRetrievalResult:
        raise error

    monkeypatch.setattr("app.cli.retrieval.getpass.getpass", lambda prompt: next(inputs))
    monkeypatch.setattr(retrieval, "_run_and_dispose", fail)

    status = retrieval.main(["inspect", "--knowledge-base-id", str(uuid4())])

    assert status == 2
    assert message in capsys.readouterr().out
