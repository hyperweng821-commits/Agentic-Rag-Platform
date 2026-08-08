"""Real-PostgreSQL vertical regressions for AF-3B hybrid retrieval."""

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)
from app.retrieval import (
    FinalCandidateValidatorLoader,
    HybridRetrievalService,
    PostgresFinalAuthoritativeLoader,
    PostgresRetrievalAccess,
    ScopedKeywordRetrievalService,
)
from app.retrieval.chroma import _DenseProviderResult as DenseProviderResult
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal

pytestmark = pytest.mark.integration

_NOW = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


class _ConnectionLedger:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        bind = sessions.kw["bind"]
        assert isinstance(bind, AsyncEngine)
        self._engine = bind.sync_engine
        self.active = 0

    def checkout(
        self,
        dbapi_connection: object,
        connection_record: object,
        connection_proxy: object,
    ) -> None:
        self.active += 1

    def checkin(self, dbapi_connection: object, connection_record: object) -> None:
        self.active -= 1

    def __enter__(self) -> "_ConnectionLedger":
        event.listen(self._engine, "checkout", self.checkout)
        event.listen(self._engine, "checkin", self.checkin)
        return self

    def __exit__(self, *args: object) -> None:
        event.remove(self._engine, "checkout", self.checkout)
        event.remove(self._engine, "checkin", self.checkin)


class _Embedding:
    model_id = "af3b-integration-fake"
    dimension = 4

    def __init__(self, connections: _ConnectionLedger) -> None:
        self.connections = connections
        self.calls = 0

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        assert self.connections.active == 0
        self.calls += 1
        return [(0.25, -0.5, 0.0, 1.0)]

    async def close(self) -> None:
        pass


class _Dense:
    def __init__(
        self,
        connections: _ConnectionLedger,
        chunk_ids: tuple[UUID, ...],
    ) -> None:
        self.connections = connections
        self.chunk_ids = chunk_ids
        self.calls = 0

    async def query(
        self,
        *,
        embedding: tuple[float, ...],
        knowledge_base_id: UUID,
        candidate_count: int,
    ) -> DenseProviderResult:
        assert self.connections.active == 0
        assert candidate_count == 40
        self.calls += 1
        return DenseProviderResult(
            position_count=len(self.chunk_ids),
            candidates=tuple(
                (f"chunk:{chunk_id}", float(index), index)
                for index, chunk_id in enumerate(self.chunk_ids)
            ),
        )


async def _seed(
    sessions: async_sessionmaker[AsyncSession],
) -> tuple[SessionAuthenticationProof, KnowledgeBase, DocumentChunk]:
    user_id = uuid4()
    session_id = uuid4()
    digest = hashlib.sha256(f"session:{session_id}".encode()).hexdigest()
    user = User(
        id=user_id,
        email=f"af3b-{user_id}@example.com",
        password_hash="$argon2id$integration-test-hash",  # noqa: S106
        is_active=True,
    )
    user_session = UserSession(
        id=session_id,
        user_id=user_id,
        token_sha256=digest,
        csrf_token_sha256=hashlib.sha256(f"csrf:{session_id}".encode()).hexdigest(),
        expires_at=_NOW + timedelta(hours=1),
    )
    knowledge_base = KnowledgeBase(id=uuid4(), name="AF-3B target")
    membership = KnowledgeBaseMembership(
        knowledge_base_id=knowledge_base.id,
        user_id=user_id,
        role=KnowledgeBaseRole.VIEWER.value,
    )
    document = Document(
        id=uuid4(),
        knowledge_base_id=knowledge_base.id,
        original_filename="authoritative.txt",
        media_type="text/plain",
        size_bytes=20,
        sha256=hashlib.sha256(b"alpha authoritative").hexdigest(),
        storage_key="private/storage/key",
        status=DocumentStatus.COMPLETED.value,
    )
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document.id,
        chunk_index=0,
        normalized_text="alpha authoritative",
        token_count=2,
        content_sha256=hashlib.sha256(b"alpha authoritative").hexdigest(),
        start_offset=0,
        end_offset=19,
        page_start=1,
        page_end=1,
    )
    async with sessions() as session, session.begin():
        session.add_all([user, user_session, knowledge_base, membership, document, chunk])
    proof = SessionAuthenticationProof(
        principal=Principal(user_id=user_id, email=user.email, session_id=session_id),
        session_token_sha256=digest,
    )
    return proof, knowledge_base, chunk


async def test_hybrid_pipeline_releases_database_and_silently_discards_stale_dense_id(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    proof, knowledge_base, chunk = await _seed(postgres_sessions)
    stale_chunk_id = uuid4()
    with _ConnectionLedger(postgres_sessions) as connections:
        embedding = _Embedding(connections)
        dense = _Dense(connections, (stale_chunk_id, chunk.id))
        service = HybridRetrievalService(
            keyword_service=ScopedKeywordRetrievalService(
                PostgresRetrievalAccess(postgres_sessions, clock=lambda: _NOW)
            ),
            embedding_model=embedding,
            dense_retrieval=dense,
            final_validator=FinalCandidateValidatorLoader(
                PostgresFinalAuthoritativeLoader(postgres_sessions, clock=lambda: _NOW)
            ),
        )

        result = await service.retrieve(
            proof=proof,
            knowledge_base_id=knowledge_base.id,
            payload={"query": "alpha", "requested_count": 10},
        )

        assert connections.active == 0
    assert embedding.calls == 1
    assert dense.calls == 1
    assert len(result.records) == 1
    record = result.records[0]
    assert record.authoritative.trusted.chunk_id == chunk.id
    assert record.keyword_rank == 1
    assert record.dense_rank == 2
    assert record.authoritative.document_content.text == "alpha authoritative"
    assert not hasattr(result, "removed_candidate_ids")
    assert str(stale_chunk_id) not in repr(result)
