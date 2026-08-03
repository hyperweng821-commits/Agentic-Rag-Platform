"""Real-PostgreSQL acceptance tests for the AF-3A-03 bounded slice."""

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from tests.retrieval_security import (
    CanonicalAcceptanceTuple,
    acceptance_tuple,
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
    MAX_KEYWORD_CANDIDATES,
    KeywordCandidate,
    PostgresRetrievalAccess,
    RetrievalAuthenticationError,
    RetrievalRequestValidationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    ScopedKeywordRetrievalService,
)
from app.security.authentication import SessionAuthenticationProof
from app.security.principal import Principal

pytestmark = pytest.mark.integration

_NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _Identity:
    user: User
    user_session: UserSession
    proof: SessionAuthenticationProof


def _identity(
    email: str,
    *,
    active: bool = True,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> _Identity:
    user_id = uuid4()
    session_id = uuid4()
    token_digest = hashlib.sha256(f"session:{email}".encode()).hexdigest()
    user = User(
        id=user_id,
        email=email,
        password_hash="$argon2id$integration-test-hash",  # noqa: S106
        is_active=active,
    )
    user_session = UserSession(
        id=session_id,
        user_id=user_id,
        token_sha256=token_digest,
        csrf_token_sha256=hashlib.sha256(f"csrf:{email}".encode()).hexdigest(),
        expires_at=expires_at or (_NOW + timedelta(hours=1)),
        revoked_at=revoked_at,
    )
    proof = SessionAuthenticationProof(
        principal=Principal(user_id=user_id, email=email, session_id=session_id),
        session_token_sha256=token_digest,
    )
    return _Identity(user=user, user_session=user_session, proof=proof)


def _document(
    knowledge_base_id: UUID,
    *,
    name: str,
    status: DocumentStatus = DocumentStatus.COMPLETED,
) -> Document:
    digest = hashlib.sha256(f"document:{knowledge_base_id}:{name}".encode()).hexdigest()
    return Document(
        id=uuid4(),
        knowledge_base_id=knowledge_base_id,
        original_filename=f"{name}.txt",
        media_type="text/plain",
        size_bytes=10,
        sha256=digest,
        storage_key=f"{knowledge_base_id}/{name}.txt",
        status=status.value,
    )


def _chunk(
    document_id: UUID,
    *,
    chunk_id: UUID | None = None,
    chunk_index: int = 0,
    normalized_text: str = "alpha keyword",
    content_sha256: str | None = "a" * 64,
) -> DocumentChunk:
    return DocumentChunk(
        id=chunk_id or uuid4(),
        document_id=document_id,
        chunk_index=chunk_index,
        normalized_text=normalized_text,
        token_count=2,
        content_sha256=content_sha256,
    )


def _access(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> PostgresRetrievalAccess:
    return PostgresRetrievalAccess(postgres_sessions, clock=lambda: _NOW)


@contextmanager
def _capture_sql_statements(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> Iterator[list[str]]:
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    try:
        yield statements
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)


@contextmanager
def _capture_database_lifecycle(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> Iterator[tuple[list[str], list[str]]]:
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    resource_events: list[str] = []
    transaction_events: list[str] = []

    def on_checkout(*args: object) -> None:
        resource_events.append("checkout")

    def on_checkin(*args: object) -> None:
        resource_events.append("checkin")

    def on_begin(*args: object) -> None:
        transaction_events.append("begin")

    def on_commit(*args: object) -> None:
        transaction_events.append("commit")

    def on_rollback(*args: object) -> None:
        transaction_events.append("rollback")

    event.listen(bind.sync_engine.pool, "checkout", on_checkout)
    event.listen(bind.sync_engine.pool, "checkin", on_checkin)
    event.listen(bind.sync_engine, "begin", on_begin)
    event.listen(bind.sync_engine, "commit", on_commit)
    event.listen(bind.sync_engine, "rollback", on_rollback)
    try:
        yield resource_events, transaction_events
    finally:
        event.remove(bind.sync_engine.pool, "checkout", on_checkout)
        event.remove(bind.sync_engine.pool, "checkin", on_checkin)
        event.remove(bind.sync_engine, "begin", on_begin)
        event.remove(bind.sync_engine, "commit", on_commit)
        event.remove(bind.sync_engine, "rollback", on_rollback)


def _pg_tuple(case_id: str, variant: str) -> CanonicalAcceptanceTuple:
    return acceptance_tuple(case_id, variant, "PostgreSQL integration")


def _pytest_param(
    canonical_tuple: CanonicalAcceptanceTuple,
    *values: object,
    suffix: str | None = None,
) -> object:
    test_id = canonical_tuple.pytest_id
    if suffix is not None:
        test_id = f"{test_id}-{suffix}"
    return pytest.param(canonical_tuple, *values, id=test_id)


class _ScopedAccessSpy:
    def __init__(self, access: PostgresRetrievalAccess) -> None:
        self._access = access
        self.calls: list[str] = []

    async def verify_initial_access(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
    ) -> None:
        self.calls.append("verify_initial_access")
        await self._access.verify_initial_access(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
        )

    async def scoped_keyword_candidates(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        normalized_query: str,
    ) -> tuple[KeywordCandidate, ...]:
        self.calls.append("scoped_keyword_candidates")
        return await self._access.scoped_keyword_candidates(
            proof=proof,
            knowledge_base_id=knowledge_base_id,
            normalized_query=normalized_query,
        )


@pytest.mark.parametrize(
    ("canonical_tuple", "invalid_state"),
    [
        _pytest_param(_pg_tuple("RET-AUTH-002", "DEFAULT"), "expired"),
        _pytest_param(_pg_tuple("RET-AUTH-003", "DEFAULT"), "inactive"),
        _pytest_param(_pg_tuple("RET-AUTH-011", "DEFAULT"), "revoked"),
    ],
)
async def test_initial_access_rejects_unusable_session_before_target(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    invalid_state: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity(
        f"{invalid_state}@example.com",
        active=invalid_state != "inactive",
        expires_at=_NOW if invalid_state == "expired" else None,
        revoked_at=_NOW - timedelta(seconds=1) if invalid_state == "revoked" else None,
    )
    knowledge_base = KnowledgeBase(id=uuid4(), name="Private")
    document = _document(knowledge_base.id, name=f"{invalid_state}-eligible")
    chunk = _chunk(document.id)
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                document,
                chunk,
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    try:
        with pytest.raises(
            RetrievalAuthenticationError,
            match="Retrieval authentication failed",
        ) as captured:
            await _access(postgres_sessions).verify_initial_access(
                proof=identity.proof,
                knowledge_base_id=knowledge_base.id,
            )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)

    assert not any("FROM knowledge_bases" in statement for statement in statements)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            str(document.id),
            str(chunk.id),
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": captured.value,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "role"),
    [
        _pytest_param(
            _pg_tuple("RET-AUTH-004", "AF3A-ROLE-MATRIX"),
            role,
            suffix=role.value,
        )
        for role in KnowledgeBaseRole
    ],
)
async def test_initial_access_accepts_exact_current_read_role_matrix(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    role: KnowledgeBaseRole,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity(f"{role.value}@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name=f"Role {role.value}")
    document = _document(knowledge_base.id, name=f"role-{role.value}")
    chunk = _chunk(document.id)
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=role.value,
                ),
                document,
                chunk,
            ]
        )

    with _capture_sql_statements(postgres_sessions) as statements:
        result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
            proof=identity.proof,
            knowledge_base_id=knowledge_base.id,
            payload={"query": "alpha", "requested_count": 1},
        )

    assert [candidate.chunk_id for candidate in result.candidates] == [chunk.id]
    assert result.candidates[0].keyword_rank == 1
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            str(document.id),
            str(chunk.id),
            "alpha",
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "target_kind", "authority_field"),
    [
        _pytest_param(
            _pg_tuple("RET-AUTH-005", "AF3A-NONMEMBER-INITIAL-ACCESS"),
            "owned",
            None,
        ),
        _pytest_param(_pg_tuple("RET-AUTH-006", "DEFAULT"), "unowned", None),
        _pytest_param(_pg_tuple("RET-AUTH-007", "DEFAULT"), "owned", "document_id"),
        _pytest_param(_pg_tuple("RET-AUTH-008", "DEFAULT"), "owned", "chunk_id"),
    ],
)
async def test_initial_access_hidden_target_cases_fail_before_keyword(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    target_kind: str,
    authority_field: str | None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    caller = _identity(f"caller-{canonical_tuple.case_id.lower()}@example.com")
    owner = _identity(f"owner-{canonical_tuple.case_id.lower()}@example.com")
    owned = KnowledgeBase(id=uuid4(), name="Owned private target")
    unowned = KnowledgeBase(id=uuid4(), name="Legacy unowned target")
    document = _document(owned.id, name="private-document")
    chunk = _chunk(document.id)
    unowned_document = _document(unowned.id, name="legacy-eligible")
    unowned_chunk = _chunk(unowned_document.id)
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                caller.user,
                caller.user_session,
                owner.user,
                owner.user_session,
                owned,
                unowned,
                KnowledgeBaseMembership(
                    knowledge_base_id=owned.id,
                    user_id=owner.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                document,
                chunk,
                unowned_document,
                unowned_chunk,
            ]
        )

    target_id = owned.id if target_kind == "owned" else unowned.id
    raw_query = f"\u00a0hidden-{canonical_tuple.case_id.lower()}-e\u0301\tpayload\u3000"
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    try:
        with pytest.raises(RetrievalTargetNotFoundError, match="target was not found") as captured:
            if authority_field is None:
                await _access(postgres_sessions).verify_initial_access(
                    proof=caller.proof,
                    knowledge_base_id=target_id,
                )
            else:
                authority_value = document.id if authority_field == "document_id" else chunk.id
                await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
                    proof=caller.proof,
                    knowledge_base_id=target_id,
                    payload={"query": raw_query, authority_field: str(authority_value)},
                )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)

    assert not any("eligible_keyword_candidates" in statement for statement in statements)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(caller.user.id),
            str(caller.user_session.id),
            caller.proof.session_token_sha256,
            str(target_id),
            str(document.id),
            str(chunk.id),
            str(unowned_document.id),
            str(unowned_chunk.id),
            *((raw_query,) if authority_field is not None else ()),
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": captured.value,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [_pytest_param(_pg_tuple("RET-AUTH-010", "AF3A-INITIAL-ACCESS-ZERO-HIT"))],
)
async def test_initial_access_succeeds_without_any_candidate_hit(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity("zero-hit@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Authorized zero hit")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
            ]
        )

    with (
        _capture_sql_statements(postgres_sessions) as statements,
        _capture_database_lifecycle(postgres_sessions) as lifecycle,
    ):
        result = await _access(postgres_sessions).verify_initial_access(
            proof=identity.proof,
            knowledge_base_id=knowledge_base.id,
        )

    assert result is None
    assert lifecycle[0] == ["checkout", "checkin"]
    assert lifecycle[1] == ["begin", "commit"]
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "raw_query"),
    [
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-EMBEDDED-U0000-GATE-ORDER"),
            "a\u0000b",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER"),
            "a" * 2_049,
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-U0000-ALONE-GATE-ORDER"),
            "\u0000",
        ),
    ],
)
async def test_invalid_query_runs_initial_access_then_releases_before_keyword(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    raw_query: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity(f"invalid-{canonical_tuple.variant.lower()}@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Invalid query gate")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []
    lifecycle: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    def on_checkout(*args: object) -> None:
        lifecycle.append("checkout")

    def on_checkin(*args: object) -> None:
        lifecycle.append("checkin")

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    event.listen(bind.sync_engine.pool, "checkout", on_checkout)
    event.listen(bind.sync_engine.pool, "checkin", on_checkin)
    try:
        with pytest.raises(RetrievalRequestValidationError) as captured:
            await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
                proof=identity.proof,
                knowledge_base_id=knowledge_base.id,
                payload={"query": raw_query},
            )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)
        event.remove(bind.sync_engine.pool, "checkout", on_checkout)
        event.remove(bind.sync_engine.pool, "checkin", on_checkin)

    assert lifecycle == ["checkout", "checkin"]
    assert not any("eligible_keyword_candidates" in statement for statement in statements)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            raw_query,
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": captured.value,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [_pytest_param(_pg_tuple("RET-AUTH-009", "AF3A-KEYWORD-EXACT-TARGET"))],
)
async def test_keyword_query_is_exact_target_scoped_eligible_and_separately_resourced(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity("member@example.com")
    target = KnowledgeBase(id=uuid4(), name="Target A")
    other = KnowledgeBase(id=uuid4(), name="Target B")
    target_valid = _document(target.id, name="target-valid")
    target_pending = _document(target.id, name="target-pending", status=DocumentStatus.PENDING)
    target_null_hash = _document(target.id, name="target-null-hash")
    other_valid = _document(other.id, name="other-valid")
    target_chunk = _chunk(target_valid.id)
    pending_chunk = _chunk(target_pending.id)
    null_hash_chunk = _chunk(target_null_hash.id, content_sha256=None)
    other_chunk = _chunk(other_valid.id)
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                target,
                other,
                KnowledgeBaseMembership(
                    knowledge_base_id=target.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=other.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
                target_valid,
                target_pending,
                target_null_hash,
                other_valid,
                target_chunk,
                pending_chunk,
                null_hash_chunk,
                other_chunk,
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    lifecycle: list[str] = []

    def on_checkout(*args: object) -> None:
        lifecycle.append("checkout")

    def on_checkin(*args: object) -> None:
        lifecycle.append("checkin")

    with _capture_sql_statements(postgres_sessions) as statements:
        event.listen(bind.sync_engine.pool, "checkout", on_checkout)
        event.listen(bind.sync_engine.pool, "checkin", on_checkin)
        try:
            result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
                proof=identity.proof,
                knowledge_base_id=target.id,
                payload={"query": "alpha", "requested_count": 1},
            )
        finally:
            event.remove(bind.sync_engine.pool, "checkout", on_checkout)
            event.remove(bind.sync_engine.pool, "checkin", on_checkin)

    assert len(result.candidates) == 1
    assert result.candidates[0].chunk_id == target_chunk.id
    assert result.candidates[0].keyword_rank == 1
    assert pending_chunk.id not in {candidate.chunk_id for candidate in result.candidates}
    assert null_hash_chunk.id not in {candidate.chunk_id for candidate in result.candidates}
    assert other_chunk.id not in {candidate.chunk_id for candidate in result.candidates}
    assert lifecycle == ["checkout", "checkin", "checkout", "checkin"]
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(target.id),
            str(other.id),
            str(target_chunk.id),
            str(pending_chunk.id),
            str(null_hash_chunk.id),
            str(other_chunk.id),
            result.request.normalized_query,
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "raw_query", "expected_query"),
    [
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-CASE-SENSITIVE"),
            "AgentForge agentforge",
            "AgentForge agentforge",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-EXCLUDED-U200B"),
            "\u200balpha\u200b\u200bbeta\u200b",
            "\u200balpha\u200b\u200bbeta\u200b",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE"),
            "\u00a0a\t \n b\u3000",
            "a b",
            suffix="exact-whitespace",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE"),
            "e\u0301",
            "é",
            suffix="decomposed-nfc",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE"),
            "é",
            "é",
            suffix="precomposed-nfc",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-NO-NFKC"),
            "\uff21gent",
            "\uff21gent",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-001", "AF3A-KEYWORD-BIND-POST-NORMALIZATION-BOUNDARY"),
            "\t" + ("a" * 2_048) + "\u3000",
            "a" * 2_048,
        ),
    ],
)
async def test_exact_normalized_query_fixture_is_bound_without_interpolation(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    raw_query: str,
    expected_query: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity("binding@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Binding")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    captured_queries: list[str] = []
    statements: list[str] = []
    lifecycle: list[str] = []

    def capture_parameters(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)
        compiled_parameters = getattr(context, "compiled_parameters", ())
        for compiled in compiled_parameters:
            normalized_query = compiled.get("normalized_query")
            if isinstance(normalized_query, str):
                captured_queries.append(normalized_query)

    def on_checkout(*args: object) -> None:
        lifecycle.append("checkout")

    def on_checkin(*args: object) -> None:
        lifecycle.append("checkin")

    event.listen(bind.sync_engine, "before_cursor_execute", capture_parameters)
    event.listen(bind.sync_engine.pool, "checkout", on_checkout)
    event.listen(bind.sync_engine.pool, "checkin", on_checkin)
    try:
        result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
            proof=identity.proof,
            knowledge_base_id=knowledge_base.id,
            payload={"query": raw_query},
        )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_parameters)
        event.remove(bind.sync_engine.pool, "checkout", on_checkout)
        event.remove(bind.sync_engine.pool, "checkin", on_checkin)

    assert captured_queries == [expected_query]
    assert result.request.normalized_query == expected_query
    assert lifecycle == ["checkout", "checkin", "checkout", "checkin"]
    assert all(raw_query not in statement for statement in statements)
    for query_sentinel in dict.fromkeys((raw_query, expected_query)):
        assert_r24_sidecar(
            canonical_tuple,
            sentinels=(
                query_sentinel,
                str(identity.user.id),
                str(identity.user_session.id),
                identity.proof.session_token_sha256,
                str(knowledge_base.id),
            ),
            log_records=caplog.records,
            sinks={
                "exception_error_records": (),
                "trace_span_names_attributes_status_events": (),
                "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
                "service_diagnostics": repr(result),
                "internal_authoritative_retrieval_record_diagnostics": (),
            },
        )


@pytest.mark.parametrize(
    ("canonical_tuple", "invalid_count"),
    [
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            0,
            suffix="zero",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            -1,
            suffix="negative-one",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            51,
            suffix="plus-one",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            True,
            suffix="boolean",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            1.0,
            suffix="float",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-003", "AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD"),
            "1",
            suffix="string",
        ),
    ],
)
async def test_invalid_count_runs_real_initial_access_but_no_keyword_sql(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    invalid_count: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity(f"invalid-count-{type(invalid_count).__name__}@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Invalid requested count")
    raw_query = "\u00a0invalid-count-raw-e\u0301\tpayload\u3000"
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []
    lifecycle: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    def on_checkout(*args: object) -> None:
        lifecycle.append("checkout")

    def on_checkin(*args: object) -> None:
        lifecycle.append("checkin")

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    event.listen(bind.sync_engine.pool, "checkout", on_checkout)
    event.listen(bind.sync_engine.pool, "checkin", on_checkin)
    try:
        with pytest.raises(RetrievalRequestValidationError) as captured:
            await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
                proof=identity.proof,
                knowledge_base_id=knowledge_base.id,
                payload={"query": raw_query, "requested_count": invalid_count},
            )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)
        event.remove(bind.sync_engine.pool, "checkout", on_checkout)
        event.remove(bind.sync_engine.pool, "checkin", on_checkin)

    assert lifecycle == ["checkout", "checkin"]
    assert not any("eligible_keyword_candidates" in statement for statement in statements)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            raw_query,
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": captured.value,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": (),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "requested_count"),
    [
        _pytest_param(
            _pg_tuple(
                "RET-BND-003",
                "AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT",
            ),
            1,
            suffix="minimum-1",
        ),
        _pytest_param(
            _pg_tuple(
                "RET-BND-003",
                "AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT",
            ),
            None,
            suffix="default-10",
        ),
        _pytest_param(
            _pg_tuple(
                "RET-BND-003",
                "AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT",
            ),
            50,
            suffix="maximum-50",
        ),
        _pytest_param(
            _pg_tuple("RET-BND-006", "AF3A-KEYWORD-LIMIT-EXACT-128"),
            1,
        ),
    ],
)
async def test_keyword_cutoff_is_independent_of_requested_count(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    requested_count: int | None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity("cutoff@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Cutoff")
    document = _document(knowledge_base.id, name="cutoff")
    chunk_ids = [UUID(int=index) for index in range(1, 130)]
    chunks = [
        _chunk(
            document.id,
            chunk_id=chunk_id,
            chunk_index=index,
            normalized_text="equal alpha score",
        )
        for index, chunk_id in reversed(list(enumerate(chunk_ids)))
    ]
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                document,
                *chunks,
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    try:
        payload: dict[str, object] = {"query": "alpha"}
        if requested_count is not None:
            payload["requested_count"] = requested_count
        result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
            proof=identity.proof,
            knowledge_base_id=knowledge_base.id,
            payload=payload,
        )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)

    if canonical_tuple.case_id == "RET-BND-003":
        expected_count = 10 if requested_count is None else requested_count
        assert result.request.requested_count == expected_count
        assert len(result.candidates) == MAX_KEYWORD_CANDIDATES
    else:
        assert len(result.candidates) == 128
        assert result.candidates[-1].keyword_rank == 128

    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            *(str(chunk_id) for chunk_id in chunk_ids),
            "alpha",
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    ("canonical_tuple", "fixture_order"),
    [
        _pytest_param(
            _pg_tuple("RET-KEY-001", "AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF"),
            "forward",
            suffix="forward-heap",
        ),
        _pytest_param(
            _pg_tuple("RET-KEY-001", "AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF"),
            "reverse",
            suffix="reverse-heap",
        ),
        _pytest_param(
            _pg_tuple("RET-KEY-001", "AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF"),
            "cutoff-hostile",
            suffix="prelimit-exposure",
        ),
    ],
)
async def test_keyword_scope_total_order_and_cutoff_match_independent_oracle(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    fixture_order: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity(f"order-{fixture_order}@example.com")
    target = KnowledgeBase(id=uuid4(), name=f"Ordered target {fixture_order}")
    other = KnowledgeBase(id=uuid4(), name=f"Excluded target {fixture_order}")
    target_document = _document(target.id, name=f"ordered-{fixture_order}")
    other_document = _document(other.id, name=f"excluded-{fixture_order}")

    high_specs = [(UUID(int=1_000 + index), index, "alpha alpha", 2) for index in range(127)]
    cutoff_specs = [
        (UUID(int=5_000), 127, "alpha", 1),
        (UUID(int=5_001), 128, "alpha", 1),
    ]
    target_specs = [*high_specs, *cutoff_specs]
    if fixture_order == "forward":
        insertion_specs = target_specs
    elif fixture_order == "reverse":
        insertion_specs = list(reversed(target_specs))
    else:
        insertion_specs = [*cutoff_specs, *reversed(high_specs)]

    target_chunks = [
        _chunk(
            target_document.id,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            normalized_text=normalized_text,
        )
        for chunk_id, chunk_index, normalized_text, _score_group in insertion_specs
    ]
    other_chunks = [
        _chunk(
            other_document.id,
            chunk_id=UUID(int=10 + index),
            chunk_index=index,
            normalized_text=normalized_text,
        )
        for index, normalized_text in enumerate(("alpha alpha", "alpha alpha alpha"))
    ]
    invalid_hash = "F" * 64
    invalid_hash_chunk = _chunk(
        target_document.id,
        chunk_id=UUID(int=6_000),
        chunk_index=129,
        normalized_text="alpha",
        content_sha256=invalid_hash,
    )

    async with postgres_sessions() as session, session.begin():
        # Prove query-level eligibility independently of the current migration constraint.
        await session.execute(
            text(
                "ALTER TABLE document_chunks "
                "DROP CONSTRAINT ck_document_chunks_valid_content_sha256"
            )
        )
        session.add_all(
            [
                identity.user,
                identity.user_session,
                target,
                other,
                KnowledgeBaseMembership(
                    knowledge_base_id=target.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=other.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
                target_document,
                other_document,
                *target_chunks,
                *other_chunks,
                invalid_hash_chunk,
            ]
        )

    async with postgres_sessions() as session:
        persisted_invalid_hash = await session.scalar(
            text("SELECT content_sha256 FROM document_chunks WHERE id = :chunk_id"),
            {"chunk_id": invalid_hash_chunk.id},
        )
        score_row = (
            await session.execute(
                text(
                    "SELECT "
                    "ts_rank_cd(to_tsvector('simple', :high_text), "
                    "plainto_tsquery('simple', :query), 0) AS high_score, "
                    "ts_rank_cd(to_tsvector('simple', :low_text), "
                    "plainto_tsquery('simple', :query), 0) AS low_score"
                ),
                {"high_text": "alpha alpha", "low_text": "alpha", "query": "alpha"},
            )
        ).one()
    assert persisted_invalid_hash == invalid_hash
    assert score_row.high_score > score_row.low_score > 0

    expected_full_order = sorted(
        target_specs,
        key=lambda spec: (-spec[3], spec[0].int),
    )
    expected_ids = [spec[0] for spec in expected_full_order[:MAX_KEYWORD_CANDIDATES]]
    assert expected_ids[-1] == cutoff_specs[0][0]
    assert cutoff_specs[1][0] not in expected_ids

    with _capture_sql_statements(postgres_sessions) as statements:
        result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
            proof=identity.proof,
            knowledge_base_id=target.id,
            payload={"query": "alpha", "requested_count": 1},
        )

    assert [candidate.chunk_id for candidate in result.candidates] == expected_ids
    assert [candidate.keyword_rank for candidate in result.candidates] == list(range(1, 129))
    assert not {chunk.id for chunk in other_chunks} & {
        candidate.chunk_id for candidate in result.candidates
    }
    assert invalid_hash_chunk.id not in {candidate.chunk_id for candidate in result.candidates}
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(target.id),
            str(other.id),
            str(target_document.id),
            str(other_document.id),
            *(str(spec[0]) for spec in target_specs),
            *(str(chunk.id) for chunk in other_chunks),
            str(invalid_hash_chunk.id),
            invalid_hash,
            "alpha",
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [_pytest_param(_pg_tuple("RET-KEY-003", "AF3A-NO-GLOBAL-RESULT-COUNT"))],
)
async def test_keyword_zero_hit_does_not_observe_inaccessible_global_count(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    caller = _identity("scoped-count-caller@example.com")
    other_owner = _identity("scoped-count-owner@example.com")
    target = KnowledgeBase(id=uuid4(), name="Authorized empty target")
    other = KnowledgeBase(id=uuid4(), name="Inaccessible match-heavy target")
    other_document = _document(other.id, name="many-private-matches")
    other_chunk_ids = [UUID(int=10_000 + index) for index in range(129)]
    other_chunks = [
        _chunk(
            other_document.id,
            chunk_id=chunk_id,
            chunk_index=index,
            normalized_text="alpha private match",
        )
        for index, chunk_id in enumerate(other_chunk_ids)
    ]
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                caller.user,
                caller.user_session,
                other_owner.user,
                other_owner.user_session,
                target,
                other,
                KnowledgeBaseMembership(
                    knowledge_base_id=target.id,
                    user_id=caller.user.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=other.id,
                    user_id=other_owner.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                other_document,
                *other_chunks,
            ]
        )

    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def capture_statement(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(bind.sync_engine, "before_cursor_execute", capture_statement)
    try:
        result = await ScopedKeywordRetrievalService(_access(postgres_sessions)).retrieve(
            proof=caller.proof,
            knowledge_base_id=target.id,
            payload={"query": "alpha"},
        )
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture_statement)

    assert result.candidates == ()
    assert not any("count(" in statement.lower() for statement in statements)
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(caller.user.id),
            str(caller.user_session.id),
            caller.proof.session_token_sha256,
            str(target.id),
            str(other.id),
            str(other_owner.user.id),
            str(other_document.id),
            *(str(chunk_id) for chunk_id in other_chunk_ids),
            "alpha",
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [_pytest_param(_pg_tuple("RET-KEY-004", "AF3A-SCOPED-REPOSITORY-ONLY"))],
)
async def test_user_facing_service_calls_only_scoped_postgres_access(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    identity = _identity("scoped-repository@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Scoped repository")
    document = _document(knowledge_base.id, name="scoped")
    chunk = _chunk(document.id)
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                document,
                chunk,
            ]
        )

    access_spy = _ScopedAccessSpy(_access(postgres_sessions))
    with _capture_sql_statements(postgres_sessions) as statements:
        result = await ScopedKeywordRetrievalService(access_spy).retrieve(
            proof=identity.proof,
            knowledge_base_id=knowledge_base.id,
            payload={"query": "alpha"},
        )

    assert access_spy.calls == ["verify_initial_access", "scoped_keyword_candidates"]
    assert [candidate.chunk_id for candidate in result.candidates] == [chunk.id]
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            str(document.id),
            str(chunk.id),
            "alpha",
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": (),
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(result),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )


@pytest.mark.parametrize(
    "canonical_tuple",
    [
        _pytest_param(
            _pg_tuple(
                "RET-PRIV-004",
                "KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY",
            )
        )
    ],
)
async def test_keyword_database_failure_is_fixed_and_all_sink_secret(
    postgres_sessions: async_sessionmaker[AsyncSession],
    canonical_tuple: CanonicalAcceptanceTuple,
    caplog: pytest.LogCaptureFixture,
) -> None:
    arm_r24_log_capture(caplog)
    raw_query = "\u00a0raw-7c6f54f8-e\u0301\t private\u3000"
    normalized_query = "raw-7c6f54f8-é private"
    identity = _identity("failure@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Failure")
    document = _document(knowledge_base.id, name="keyword-fatal-eligible")
    persisted_content_hash = hashlib.sha256(b"keyword-fatal-eligible-content").hexdigest()
    chunk = _chunk(
        document.id,
        normalized_text=normalized_query,
        content_sha256=persisted_content_hash,
    )
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                identity.user,
                identity.user_session,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=identity.user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                document,
                chunk,
            ]
        )

    database_sentinel = "database-2dd09bf3688f47ba82a3c59e13fd147d"
    driver_sentinel = "driver-309d72b1fd3d44d6b7c83b09697093da"
    transaction_sentinel = "transaction-6c9d240493eb4cca94f6c3fe3054a4df"
    bind = postgres_sessions.kw["bind"]
    assert isinstance(bind, AsyncEngine)
    statements: list[str] = []

    def inject_keyword_failure(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)
        if "eligible_keyword_candidates" in statement:
            raise SQLAlchemyError(f"{database_sentinel}|{driver_sentinel}|{transaction_sentinel}")

    access_spy = _ScopedAccessSpy(_access(postgres_sessions))
    with _capture_database_lifecycle(postgres_sessions) as lifecycle:
        event.listen(bind.sync_engine, "before_cursor_execute", inject_keyword_failure)
        try:
            with pytest.raises(RetrievalUnavailableError) as captured:
                await ScopedKeywordRetrievalService(access_spy).retrieve(
                    proof=identity.proof,
                    knowledge_base_id=knowledge_base.id,
                    payload={"query": raw_query},
                )
        finally:
            event.remove(bind.sync_engine, "before_cursor_execute", inject_keyword_failure)

    assert str(captured.value) == "Retrieval is unavailable."
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert captured.value.__suppress_context__ is False
    assert access_spy.calls == ["verify_initial_access", "scoped_keyword_candidates"]
    assert lifecycle[0] == ["checkout", "checkin", "checkout", "checkin"]
    assert lifecycle[1] == ["begin", "commit", "begin", "rollback"]
    assert sum("eligible_keyword_candidates" in statement for statement in statements) == 1
    assert "eligible_keyword_candidates" in statements[-1]
    assert_r24_sidecar(
        canonical_tuple,
        sentinels=(
            raw_query,
            normalized_query,
            database_sentinel,
            driver_sentinel,
            transaction_sentinel,
            str(identity.user.id),
            str(identity.user_session.id),
            identity.proof.session_token_sha256,
            str(knowledge_base.id),
            str(document.id),
            document.sha256,
            str(chunk.id),
            persisted_content_hash,
        ),
        log_records=caplog.records,
        sinks={
            "exception_error_records": captured.value,
            "trace_span_names_attributes_status_events": (),
            "postgres_sql_database_driver_transaction_diagnostics": tuple(statements),
            "service_diagnostics": repr(captured.value),
            "internal_authoritative_retrieval_record_diagnostics": (),
        },
    )
