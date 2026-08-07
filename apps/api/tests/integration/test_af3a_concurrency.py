"""Deterministic real-PostgreSQL AF-3A-05 snapshot and concurrency gates."""

import asyncio
import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import TracebackType
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from tests.retrieval_security import (
    CanonicalAcceptanceTuple,
    af3a05_acceptance_tuple,
    arm_r24_log_capture,
    assert_r24_sidecar,
)

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
    PostgresFinalAuthoritativeLoader,
    PostgresRetrievalAccess,
)
from app.retrieval.service import (
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
)
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal

pytestmark = pytest.mark.integration

_FINAL_NOW = datetime(2026, 8, 6, 9, 0, tzinfo=UTC)
_BARRIER_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class _Identity:
    user: User
    session: UserSession
    proof: SessionAuthenticationProof


@dataclass(frozen=True, slots=True)
class _SeededCase:
    identity: _Identity
    knowledge_base: KnowledgeBase
    document: Document
    chunks: tuple[DocumentChunk, ...]


def _pg(case_id: str, variant: str) -> CanonicalAcceptanceTuple:
    return af3a05_acceptance_tuple(case_id, variant, "PostgreSQL integration")


def _dc(case_id: str, variant: str) -> CanonicalAcceptanceTuple:
    return af3a05_acceptance_tuple(case_id, variant, "deterministic concurrency")


_INACTIVE_BEFORE_ROW = _pg(
    "RET-CONC-003",
    "AF3A-KEYWORD-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT",
)
_DOCUMENT_BEFORE_ROWS = (
    (
        _pg("RET-CONC-004", "AF3A-KEYWORD-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT"),
        DocumentStatus.PROCESSING,
    ),
    (
        _pg("RET-CONC-004", "AF3A-KEYWORD-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT"),
        DocumentStatus.FAILED,
    ),
)
_CHUNK_BEFORE_ROW = _pg(
    "RET-CONC-005",
    "AF3A-KEYWORD-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT",
)
_MEMBERSHIP_AFTER_ROW = _pg(
    "RET-CONC-006",
    "AF3A-SYNTHETIC-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT",
)
_DOCUMENT_AFTER_ROW = _pg(
    "RET-CONC-007",
    "AF3A-KEYWORD-DOCUMENT-CHANGED-AFTER-SNAPSHOT",
)
_CHUNK_AFTER_ROW = _pg(
    "RET-CONC-008",
    "AF3A-KEYWORD-CHUNK-REPLACED-AFTER-SNAPSHOT",
)
_REVOCATION_AFTER_COMMIT_ROW = _pg(
    "RET-CONC-009",
    "AF3A-KEYWORD-REVOCATION-AFTER-FINAL-COMMIT",
)
_MULTIBATCH_ROW = _pg(
    "RET-CONC-010",
    "AF3A-SYNTHETIC-MULTIBATCH-FIXED-SNAPSHOT",
)
_BATCH_FAILURE_ROW = _pg("RET-CONC-011", "AF3A-BATCH-TWO-STATEMENT-FAILURE")
_BATCH_TIMEOUT_ROW = _pg("RET-CONC-011", "AF3A-BATCH-TWO-STATEMENT-TIMEOUT")
_COMMIT_FAILURE_ROW = _pg("RET-CONC-011", "AF3A-FINAL-COMMIT-FAILURE")
_CONNECTION_FAILURE_ROW = _pg("RET-CONC-011", "AF3A-FINAL-CONNECTION-FAILURE")
_ELAPSED_EXPIRY_ROWS = (
    _pg("RET-CONC-013", "AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY"),
    _dc("RET-CONC-013", "AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY"),
)
_PHYSICAL_DELETE_ROWS = (
    _pg("RET-CONC-014", "AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT"),
    _dc("RET-CONC-014", "AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT"),
)


def _identity(*, expires_at: datetime) -> _Identity:
    user_id = uuid4()
    session_id = uuid4()
    digest = hashlib.sha256(f"af3a05-session:{session_id}".encode()).hexdigest()
    user = User(
        id=user_id,
        email=f"af3a05-{uuid4()}@example.com",
        password_hash="$argon2id$af3a05-integration-hash",  # noqa: S106
        is_active=True,
    )
    session = UserSession(
        id=session_id,
        user_id=user_id,
        token_sha256=digest,
        csrf_token_sha256=hashlib.sha256(f"af3a05-csrf:{session_id}".encode()).hexdigest(),
        expires_at=expires_at,
    )
    return _Identity(
        user=user,
        session=session,
        proof=SessionAuthenticationProof(
            principal=Principal(
                user_id=user_id,
                email=user.email,
                session_id=session_id,
            ),
            session_token_sha256=digest,
        ),
    )


def _document(knowledge_base_id: UUID) -> Document:
    marker = uuid4()
    digest = hashlib.sha256(f"af3a05-document:{marker}".encode()).hexdigest()
    return Document(
        id=uuid4(),
        knowledge_base_id=knowledge_base_id,
        original_filename=f"af3a05-source-{marker}.txt",
        media_type="text/plain",
        size_bytes=100,
        sha256=digest,
        storage_key=f"af3a05/{marker}/{digest}",
        status=DocumentStatus.COMPLETED.value,
    )


def _chunk(document_id: UUID, *, chunk_id: UUID, index: int, label: str) -> DocumentChunk:
    content = f"alpha {label} content {uuid4()}"
    return DocumentChunk(
        id=chunk_id,
        document_id=document_id,
        chunk_index=index,
        normalized_text=content,
        token_count=4,
        content_sha256=hashlib.sha256(content.encode()).hexdigest(),
        start_offset=index * 100,
        end_offset=index * 100 + len(content),
        page_start=index + 1,
        page_end=index + 1,
    )


def _candidate_ids(count: int) -> tuple[UUID, ...]:
    return tuple(
        sorted(
            uuid5(NAMESPACE_URL, f"af3a05-concurrency-candidate-{index}") for index in range(count)
        )
    )


async def _seed_case(
    postgres_sessions: async_sessionmaker[AsyncSession],
    *,
    candidate_count: int = 1,
    expires_at: datetime | None = None,
) -> _SeededCase:
    identity = _identity(expires_at=expires_at or _FINAL_NOW + timedelta(hours=1))
    knowledge_base = KnowledgeBase(id=uuid4(), name=f"AF3A05 target {uuid4()}")
    membership = KnowledgeBaseMembership(
        knowledge_base_id=knowledge_base.id,
        user_id=identity.user.id,
        role=KnowledgeBaseRole.VIEWER.value,
    )
    document = _document(knowledge_base.id)
    chunks = tuple(
        _chunk(
            document.id,
            chunk_id=chunk_id,
            index=index,
            label=f"old-{index}",
        )
        for index, chunk_id in enumerate(_candidate_ids(candidate_count))
    )
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [identity.user, identity.session, knowledge_base, membership, document, *chunks]
        )
    return _SeededCase(identity, knowledge_base, document, chunks)


def _access(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> PostgresRetrievalAccess:
    return PostgresRetrievalAccess(postgres_sessions, clock=lambda: _FINAL_NOW)


def _validator(
    session_factory: object,
    *,
    final_now: datetime = _FINAL_NOW,
) -> FinalCandidateValidatorLoader:
    return FinalCandidateValidatorLoader(
        PostgresFinalAuthoritativeLoader(
            session_factory,  # type: ignore[arg-type]
            clock=lambda: final_now,
        )
    )


async def _keyword_ids(
    postgres_sessions: async_sessionmaker[AsyncSession],
    seeded: _SeededCase,
) -> tuple[UUID, ...]:
    access = _access(postgres_sessions)
    await access.verify_initial_access(
        proof=seeded.identity.proof,
        knowledge_base_id=seeded.knowledge_base.id,
    )
    candidates = await access.scoped_keyword_candidates(
        proof=seeded.identity.proof,
        knowledge_base_id=seeded.knowledge_base.id,
        normalized_query="alpha",
    )
    return tuple(candidate.chunk_id for candidate in candidates)


class _BarrierSession:
    def __init__(self, session: AsyncSession, factory: "_BarrierSessionFactory") -> None:
        self._session = session
        self._factory = factory
        self._execution_count = 0

    async def __aenter__(self) -> "_BarrierSession":
        await self._session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    def begin(self) -> object:
        return self._session.begin()

    async def execute(self, *args: object, **kwargs: object) -> object:
        result = await self._session.execute(*args, **kwargs)  # type: ignore[arg-type]
        self._execution_count += 1
        self._factory.execution_count = self._execution_count
        if self._execution_count == self._factory.after_execute:
            self._factory.reached.set()
            await asyncio.wait_for(
                self._factory.release.wait(),
                timeout=_BARRIER_TIMEOUT_SECONDS,
            )
        return result


class _BarrierSessionFactory:
    def __init__(
        self,
        delegate: async_sessionmaker[AsyncSession],
        *,
        after_execute: int,
    ) -> None:
        self._delegate = delegate
        self.after_execute = after_execute
        self.execution_count = 0
        self.reached = asyncio.Event()
        self.release = asyncio.Event()

    def __call__(self) -> _BarrierSession:
        return _BarrierSession(self._delegate(), self)

    async def wait_until_reached(self) -> None:
        await asyncio.wait_for(self.reached.wait(), timeout=_BARRIER_TIMEOUT_SECONDS)


class _DelegatingSession:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._execution_count = 0

    async def __aenter__(self) -> "_DelegatingSession":
        await self._session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    def begin(self) -> object:
        return self._session.begin()

    async def execute(self, *args: object, **kwargs: object) -> object:
        self._execution_count += 1
        return await self._session.execute(*args, **kwargs)  # type: ignore[arg-type]


class _BatchFailureSession(_DelegatingSession):
    async def execute(self, *args: object, **kwargs: object) -> object:
        self._execution_count += 1
        if self._execution_count == 4:
            raise SQLAlchemyError("AF-3A final batch statement failed")
        return await self._session.execute(*args, **kwargs)  # type: ignore[arg-type]


class _BatchFailureSessionFactory:
    def __init__(self, delegate: async_sessionmaker[AsyncSession]) -> None:
        self._delegate = delegate

    def __call__(self) -> _BatchFailureSession:
        return _BatchFailureSession(self._delegate())


class _TimeoutSession(_DelegatingSession):
    def __init__(self, session: AsyncSession, *, advisory_lock_key: int) -> None:
        super().__init__(session)
        self._advisory_lock_key = advisory_lock_key

    async def execute(self, *args: object, **kwargs: object) -> object:
        self._execution_count += 1
        if self._execution_count == 4:
            await self._session.execute(text("SET LOCAL statement_timeout = '250ms'"))
            return await self._session.execute(
                text("SELECT pg_advisory_xact_lock(:advisory_lock_key)"),
                {"advisory_lock_key": self._advisory_lock_key},
            )
        return await self._session.execute(*args, **kwargs)  # type: ignore[arg-type]


class _TimeoutSessionFactory:
    def __init__(
        self,
        delegate: async_sessionmaker[AsyncSession],
        *,
        advisory_lock_key: int,
    ) -> None:
        self._delegate = delegate
        self._advisory_lock_key = advisory_lock_key

    def __call__(self) -> _TimeoutSession:
        return _TimeoutSession(
            self._delegate(),
            advisory_lock_key=self._advisory_lock_key,
        )


class _CommitFailureTransaction:
    def __init__(self, transaction: object) -> None:
        self._transaction = transaction

    async def __aenter__(self) -> object:
        return await self._transaction.__aenter__()  # type: ignore[attr-defined,no-any-return]

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> object:
        if exc_type is not None:
            return await self._transaction.__aexit__(  # type: ignore[attr-defined,no-any-return]
                exc_type,
                exc_value,
                traceback,
            )
        failure = SQLAlchemyError("AF-3A final transaction commit failed")
        await self._transaction.__aexit__(  # type: ignore[attr-defined]
            SQLAlchemyError,
            failure,
            None,
        )
        raise failure


class _CommitFailureSession(_DelegatingSession):
    def begin(self) -> _CommitFailureTransaction:
        return _CommitFailureTransaction(self._session.begin())


class _CommitFailureSessionFactory:
    def __init__(self, delegate: async_sessionmaker[AsyncSession]) -> None:
        self._delegate = delegate

    def __call__(self) -> _CommitFailureSession:
        return _CommitFailureSession(self._delegate())


class _ConnectionFailureSessionFactory:
    def __call__(self) -> object:
        raise SQLAlchemyError("AF-3A final connection acquisition failed")


@contextmanager
def _capture_sql(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> Iterator[list[str]]:
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture)
    try:
        yield statements
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture)


def _sentinels(
    seeded: _SeededCase,
    *,
    extra_chunks: tuple[DocumentChunk, ...] = (),
) -> tuple[str, ...]:
    values = [
        str(seeded.identity.user.id),
        str(seeded.identity.session.id),
        seeded.identity.proof.session_token_sha256,
        str(seeded.knowledge_base.id),
        str(seeded.document.id),
        seeded.document.original_filename,
        seeded.document.sha256,
    ]
    for chunk in (*seeded.chunks, *extra_chunks):
        values.extend((str(chunk.id), chunk.normalized_text))
        if chunk.content_sha256 is not None:
            values.append(chunk.content_sha256)
    return tuple(dict.fromkeys(values))


def _assert_sidecar(
    canonical_tuple: CanonicalAcceptanceTuple,
    *,
    caplog: pytest.LogCaptureFixture,
    seeded: _SeededCase,
    statements: tuple[str, ...],
    records: object = (),
    exceptions: object = (),
    extra_chunks: tuple[DocumentChunk, ...] = (),
) -> None:
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=_sentinels(seeded, extra_chunks=extra_chunks),
        log_records=caplog.records,
        sinks={
            "exception_error_records": exceptions,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": statements,
            "service_diagnostics": {
                "statement_count": len(statements),
                "record_count": len(records),
                "record_types": tuple(type(record).__name__ for record in records),
            },
            "internal_authoritative_retrieval_record_diagnostics": tuple(
                repr(record) for record in records
            ),
        },
    )


async def _revoke_session(
    postgres_sessions: async_sessionmaker[AsyncSession],
    session_id: UUID,
) -> None:
    async with postgres_sessions() as session, session.begin():
        stored = await session.get(UserSession, session_id)
        assert stored is not None
        stored.revoked_at = _FINAL_NOW


async def _deactivate_user(
    postgres_sessions: async_sessionmaker[AsyncSession],
    user_id: UUID,
) -> None:
    async with postgres_sessions() as session, session.begin():
        stored = await session.get(User, user_id)
        assert stored is not None
        stored.is_active = False


async def _remove_membership(
    postgres_sessions: async_sessionmaker[AsyncSession],
    seeded: _SeededCase,
) -> None:
    async with postgres_sessions() as session, session.begin():
        membership = await session.get(
            KnowledgeBaseMembership,
            (seeded.knowledge_base.id, seeded.identity.user.id),
        )
        assert membership is not None
        await session.delete(membership)


async def _restore_membership(
    postgres_sessions: async_sessionmaker[AsyncSession],
    seeded: _SeededCase,
) -> None:
    async with postgres_sessions() as session, session.begin():
        session.add(
            KnowledgeBaseMembership(
                knowledge_base_id=seeded.knowledge_base.id,
                user_id=seeded.identity.user.id,
                role=KnowledgeBaseRole.VIEWER.value,
            )
        )


async def _change_document_status(
    postgres_sessions: async_sessionmaker[AsyncSession],
    document_id: UUID,
    status: DocumentStatus,
) -> None:
    async with postgres_sessions() as session, session.begin():
        document = await session.get(Document, document_id)
        assert document is not None
        document.status = status.value


async def _replace_chunk(
    postgres_sessions: async_sessionmaker[AsyncSession],
    old_chunk_id: UUID,
    *,
    label: str,
) -> DocumentChunk:
    async with postgres_sessions() as session, session.begin():
        old = await session.get(DocumentChunk, old_chunk_id)
        assert old is not None
        replacement = _chunk(
            old.document_id,
            chunk_id=uuid4(),
            index=old.chunk_index,
            label=label,
        )
        await session.delete(old)
        await session.flush()
        session.add(replacement)
    return replacement


async def _delete_document(
    postgres_sessions: async_sessionmaker[AsyncSession],
    document_id: UUID,
) -> None:
    async with postgres_sessions() as session, session.begin():
        document = await session.get(Document, document_id)
        assert document is not None
        await session.delete(document)


async def _remove_membership_and_replace_chunk(
    postgres_sessions: async_sessionmaker[AsyncSession],
    seeded: _SeededCase,
    old_chunk_id: UUID,
) -> DocumentChunk:
    async with postgres_sessions() as session, session.begin():
        membership = await session.get(
            KnowledgeBaseMembership,
            (seeded.knowledge_base.id, seeded.identity.user.id),
        )
        old = await session.get(DocumentChunk, old_chunk_id)
        assert membership is not None
        assert old is not None
        replacement = _chunk(
            old.document_id,
            chunk_id=uuid4(),
            index=old.chunk_index,
            label="multibatch-new",
        )
        await session.delete(membership)
        await session.delete(old)
        await session.flush()
        session.add(replacement)
    return replacement


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_INACTIVE_BEFORE_ROW, id=_INACTIVE_BEFORE_ROW.pytest_id)],
)
async def test_inactive_user_committed_before_snapshot_fails_authentication(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    assert candidate_ids == (seeded.chunks[0].id,)
    await _deactivate_user(postgres_sessions, seeded.identity.user.id)

    with (
        _capture_sql(postgres_sessions) as statements,
        pytest.raises(RetrievalAuthenticationError) as captured,
    ):
        await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert "FROM document_chunks" not in " ".join(statements)
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple,status",
    [pytest.param(*row, id=row[0].pytest_id) for row in _DOCUMENT_BEFORE_ROWS],
)
async def test_document_ineligibility_committed_before_snapshot_omits_candidate(
    canonical_tuple: CanonicalAcceptanceTuple,
    status: DocumentStatus,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    await _change_document_status(postgres_sessions, seeded.document.id, status)

    with _capture_sql(postgres_sessions) as statements:
        records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert records == ()
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=records,
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_CHUNK_BEFORE_ROW, id=_CHUNK_BEFORE_ROW.pytest_id)],
)
async def test_chunk_replacement_committed_before_snapshot_filters_stale_identity(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    replacement = await _replace_chunk(
        postgres_sessions,
        seeded.chunks[0].id,
        label="replacement-before",
    )

    with _capture_sql(postgres_sessions) as statements:
        records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert records == ()
    assert replacement.id not in tuple(record.trusted.chunk_id for record in records)
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=records,
        extra_chunks=(replacement,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(row, id=row.pytest_id) for row in _PHYSICAL_DELETE_ROWS],
)
async def test_physical_delete_committed_before_snapshot_filters_stale_keyword_candidate(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=1)

    with _capture_sql(postgres_sessions) as statements:
        operation = asyncio.create_task(
            _validator(barrier).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )
        )
        await barrier.wait_until_reached()
        try:
            await _delete_document(postgres_sessions, seeded.document.id)
        finally:
            barrier.release.set()
        records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)

    assert records == ()
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=records,
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_MEMBERSHIP_AFTER_ROW, id=_MEMBERSHIP_AFTER_ROW.pytest_id)],
)
async def test_membership_removed_after_snapshot_preserves_current_and_hides_next(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=2)

    with _capture_sql(postgres_sessions) as statements:
        operation = asyncio.create_task(
            _validator(barrier).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )
        )
        await barrier.wait_until_reached()
        try:
            await _remove_membership(postgres_sessions, seeded)
        finally:
            barrier.release.set()
        records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)
        with pytest.raises(RetrievalTargetNotFoundError) as captured:
            await _validator(postgres_sessions).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )

    assert tuple(record.trusted.chunk_id for record in records) == candidate_ids
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=records,
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_DOCUMENT_AFTER_ROW, id=_DOCUMENT_AFTER_ROW.pytest_id)],
)
async def test_document_change_after_snapshot_preserves_current_and_omits_next(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=2)

    with _capture_sql(postgres_sessions) as statements:
        operation = asyncio.create_task(
            _validator(barrier).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )
        )
        await barrier.wait_until_reached()
        try:
            await _change_document_status(
                postgres_sessions,
                seeded.document.id,
                DocumentStatus.PROCESSING,
            )
        finally:
            barrier.release.set()
        current_records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)
        later_records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert tuple(record.trusted.chunk_id for record in current_records) == candidate_ids
    assert later_records == ()
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=current_records,
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_CHUNK_AFTER_ROW, id=_CHUNK_AFTER_ROW.pytest_id)],
)
async def test_chunk_replacement_after_snapshot_preserves_old_then_exposes_new(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    old = seeded.chunks[0]
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=2)

    with _capture_sql(postgres_sessions) as statements:
        operation = asyncio.create_task(
            _validator(barrier).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )
        )
        await barrier.wait_until_reached()
        try:
            replacement = await _replace_chunk(
                postgres_sessions,
                old.id,
                label="replacement-after",
            )
        finally:
            barrier.release.set()
        current_records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)
        later_records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=(replacement.id,),
        )

    assert len(current_records) == 1
    assert current_records[0].trusted.chunk_id == old.id
    assert current_records[0].trusted.content_sha256 == old.content_sha256
    assert current_records[0].document_content.text == old.normalized_text
    assert len(later_records) == 1
    assert later_records[0].trusted.chunk_id == replacement.id
    assert later_records[0].trusted.content_sha256 == replacement.content_sha256
    assert later_records[0].document_content.text == replacement.normalized_text
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=current_records,
        extra_chunks=(replacement,),
    )


async def test_session_revoked_after_snapshot_preserves_current_and_fails_next(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    """Supplement ADR-008-R05 without inventing a new canonical ledger identity."""
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=2)
    operation = asyncio.create_task(
        _validator(barrier).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )
    )
    await barrier.wait_until_reached()
    try:
        await _revoke_session(postgres_sessions, seeded.identity.session.id)
    finally:
        barrier.release.set()
    current_records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)

    assert tuple(record.trusted.chunk_id for record in current_records) == candidate_ids
    with pytest.raises(RetrievalAuthenticationError):
        await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_REVOCATION_AFTER_COMMIT_ROW, id=_REVOCATION_AFTER_COMMIT_ROW.pytest_id)],
)
async def test_membership_revocation_after_final_commit_does_not_reload_current_records(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)

    with _capture_sql(postgres_sessions) as statements:
        records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )
        statement_count_after_commit = len(statements)
        await _remove_membership(postgres_sessions, seeded)
        statement_count_after_mutation = len(statements)
        assert statement_count_after_mutation > statement_count_after_commit
        assert records[0].document_content.text == seeded.chunks[0].normalized_text
        assert len(statements) == statement_count_after_mutation
        with pytest.raises(RetrievalTargetNotFoundError) as captured:
            await _validator(postgres_sessions).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )

    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=records,
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_MULTIBATCH_ROW, id=_MULTIBATCH_ROW.pytest_id)],
)
async def test_multiple_batches_share_fixed_snapshot_and_later_retrieval_sees_mutations(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions, candidate_count=192)
    await _access(postgres_sessions).verify_initial_access(
        proof=seeded.identity.proof,
        knowledge_base_id=seeded.knowledge_base.id,
    )
    candidate_ids = tuple(chunk.id for chunk in seeded.chunks)
    old_later_chunk = seeded.chunks[-1]
    barrier = _BarrierSessionFactory(postgres_sessions, after_execute=3)

    with _capture_sql(postgres_sessions) as statements:
        operation = asyncio.create_task(
            _validator(barrier).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )
        )
        await barrier.wait_until_reached()
        try:
            replacement = await _remove_membership_and_replace_chunk(
                postgres_sessions,
                seeded,
                old_later_chunk.id,
            )
        finally:
            barrier.release.set()
        current_records = await asyncio.wait_for(operation, timeout=_BARRIER_TIMEOUT_SECONDS)

        with pytest.raises(RetrievalTargetNotFoundError) as captured:
            await _validator(postgres_sessions).validate_and_load(
                proof=seeded.identity.proof,
                knowledge_base_id=seeded.knowledge_base.id,
                candidate_ids=candidate_ids,
            )

        await _restore_membership(postgres_sessions, seeded)
        later_candidate_ids = tuple(
            sorted(
                (
                    *(
                        candidate_id
                        for candidate_id in candidate_ids
                        if candidate_id != old_later_chunk.id
                    ),
                    replacement.id,
                ),
            )
        )
        later_records = await _validator(postgres_sessions).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=later_candidate_ids,
        )

    assert tuple(record.trusted.chunk_id for record in current_records) == candidate_ids
    assert current_records[-1].document_content.text == old_later_chunk.normalized_text
    later_ids = tuple(record.trusted.chunk_id for record in later_records)
    assert old_later_chunk.id not in later_ids
    assert replacement.id in later_ids
    assert barrier.execution_count == 5
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        records=current_records,
        exceptions=(captured.value,),
        extra_chunks=(replacement,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_BATCH_FAILURE_ROW, id=_BATCH_FAILURE_ROW.pytest_id)],
)
async def test_second_batch_database_failure_discards_first_batch_records(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions, candidate_count=65)
    candidate_ids = tuple(chunk.id for chunk in seeded.chunks)

    with (
        _capture_sql(postgres_sessions) as statements,
        pytest.raises(RetrievalUnavailableError) as captured,
    ):
        await _validator(_BatchFailureSessionFactory(postgres_sessions)).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    candidate_statements = [
        statement for statement in statements if "FROM document_chunks" in statement
    ]
    assert len(candidate_statements) == 1
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_BATCH_TIMEOUT_ROW, id=_BATCH_TIMEOUT_ROW.pytest_id)],
)
async def test_real_statement_timeout_in_second_batch_discards_first_batch_records(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions, candidate_count=65)
    candidate_ids = tuple(chunk.id for chunk in seeded.chunks)
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    advisory_lock_key = uuid4().int % (2**31 - 1)

    with _capture_sql(postgres_sessions) as statements:
        async with bind.connect() as blocker:
            await blocker.execute(
                text("SELECT pg_advisory_lock(:advisory_lock_key)"),
                {"advisory_lock_key": advisory_lock_key},
            )
            try:
                with pytest.raises(RetrievalUnavailableError) as captured:
                    await _validator(
                        _TimeoutSessionFactory(
                            postgres_sessions,
                            advisory_lock_key=advisory_lock_key,
                        )
                    ).validate_and_load(
                        proof=seeded.identity.proof,
                        knowledge_base_id=seeded.knowledge_base.id,
                        candidate_ids=candidate_ids,
                    )
            finally:
                unlocked = await blocker.scalar(
                    text("SELECT pg_advisory_unlock(:advisory_lock_key)"),
                    {"advisory_lock_key": advisory_lock_key},
                )
                assert unlocked is True

    candidate_statements = [
        statement for statement in statements if "FROM document_chunks" in statement
    ]
    assert len(candidate_statements) == 1
    assert any("SET LOCAL statement_timeout" in statement for statement in statements)
    assert any("pg_advisory_xact_lock" in statement for statement in statements)
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_COMMIT_FAILURE_ROW, id=_COMMIT_FAILURE_ROW.pytest_id)],
)
async def test_final_commit_failure_discards_loaded_records(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = tuple(chunk.id for chunk in seeded.chunks)

    with (
        _capture_sql(postgres_sessions) as statements,
        pytest.raises(RetrievalUnavailableError) as captured,
    ):
        await _validator(_CommitFailureSessionFactory(postgres_sessions)).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert any("FROM document_chunks" in statement for statement in statements)
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(_CONNECTION_FAILURE_ROW, id=_CONNECTION_FAILURE_ROW.pytest_id)],
)
async def test_final_connection_failure_stops_before_authorization_and_records(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(postgres_sessions)
    candidate_ids = tuple(chunk.id for chunk in seeded.chunks)

    with (
        _capture_sql(postgres_sessions) as statements,
        pytest.raises(RetrievalUnavailableError) as captured,
    ):
        await _validator(_ConnectionFailureSessionFactory()).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert statements == []
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [pytest.param(row, id=row.pytest_id) for row in _ELAPSED_EXPIRY_ROWS],
)
async def test_provider_independent_elapsed_barrier_expiry_uses_fresh_final_clock(
    canonical_tuple: CanonicalAcceptanceTuple,
    postgres_sessions: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    seeded = await _seed_case(
        postgres_sessions,
        expires_at=_FINAL_NOW + timedelta(minutes=1),
    )
    candidate_ids = await _keyword_ids(postgres_sessions, seeded)

    with (
        _capture_sql(postgres_sessions) as statements,
        pytest.raises(RetrievalAuthenticationError) as captured,
    ):
        await _validator(
            postgres_sessions,
            final_now=_FINAL_NOW + timedelta(minutes=2),
        ).validate_and_load(
            proof=seeded.identity.proof,
            knowledge_base_id=seeded.knowledge_base.id,
            candidate_ids=candidate_ids,
        )

    assert "FROM document_chunks" not in " ".join(statements)
    _assert_sidecar(
        canonical_tuple,
        caplog=caplog,
        seeded=seeded,
        statements=tuple(statements),
        exceptions=(captured.value,),
    )
