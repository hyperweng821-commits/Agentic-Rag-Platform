"""Focused repository query, authorization-scope, and flush tests."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
    KnowledgeBaseRole,
    User,
    UserSession,
)
from app.db.repositories import (
    DocumentChunkRepository,
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseMembershipRepository,
    KnowledgeBaseRepository,
    UserRepository,
    UserSessionRepository,
)


def _postgresql_sql(statement: object) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))  # type: ignore[attr-defined]


async def test_user_repository_separates_authentication_and_operator_queries() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    user = User(
        id=uuid4(),
        email="owner@example.com",
        password_hash="$argon2id$v=19$m=1,t=1,p=1$hash",  # noqa: S106
    )
    observed_hash = user.password_hash
    auth_result = MagicMock()
    auth_result.one_or_none.return_value = SimpleNamespace(
        id=user.id,
        email=user.email,
        is_active=True,
        password_hash=observed_hash,
    )
    session.execute.return_value = auth_result
    session.scalar.side_effect = [user, user]
    repository = UserRepository(session)

    await repository.add_for_operator(user)
    snapshot = await repository.get_for_authentication_by_email("owner@example.com")
    locked = await repository.get_locked_for_authentication(user.id)
    operator = await repository.get_for_operator_by_email(
        "owner@example.com",
        for_update=True,
    )
    replacement_hash = "$argon2id$replacement"
    await repository.update_password_hash_for_authentication(
        user,
        password_hash=replacement_hash,
    )

    assert snapshot is not None
    assert snapshot.user_id == user.id
    assert snapshot.email == user.email
    assert snapshot.is_active is True
    assert snapshot.password_hash == observed_hash
    assert locked is user
    assert operator is user
    assert user.password_hash == replacement_hash
    session.add.assert_called_once_with(user)
    assert session.flush.await_count == 2
    auth_statement = session.execute.await_args.args[0]
    assert "users.email =" in _postgresql_sql(auth_statement)
    for call in session.scalar.await_args_list:
        rendered = _postgresql_sql(call.args[0])
        assert "FROM users" in rendered
        assert "FOR UPDATE" in rendered
    session.commit.assert_not_awaited()


async def test_active_session_lookup_fences_digest_revocation_and_expiry() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    now = datetime(2026, 7, 29, 12, tzinfo=UTC)

    result = await UserSessionRepository(session).get_active_for_authentication_by_token_sha256(
        "a" * 64, now=now
    )

    assert result is None
    statement = session.scalar.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "user_sessions.token_sha256 =" in rendered
    assert "user_sessions.revoked_at IS NULL" in rendered
    assert "user_sessions.expires_at >" in rendered


async def test_session_repository_revokes_and_touches_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    now = datetime(2026, 7, 29, 12, tzinfo=UTC)
    user_session = UserSession(
        user_id=uuid4(),
        token_sha256="a" * 64,
        csrf_token_sha256="b" * 64,
        expires_at=now + timedelta(hours=1),
    )
    repository = UserSessionRepository(session)

    await repository.add_for_authentication(user_session)
    await repository.touch_for_authentication(user_session, seen_at=now)
    await repository.revoke_for_authentication(user_session, revoked_at=now)

    session.add.assert_called_once_with(user_session)
    assert user_session.last_seen_at == now
    assert user_session.revoked_at == now
    assert session.flush.await_count == 3
    session.commit.assert_not_awaited()


async def test_knowledge_base_add_with_owner_flushes_one_aggregate() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    owner_user_id = uuid4()
    knowledge_base = KnowledgeBase(name="Private")

    await KnowledgeBaseRepository(session).add_with_owner(
        knowledge_base,
        owner_user_id=owner_user_id,
    )

    session.add.assert_called_once_with(knowledge_base)
    assert len(knowledge_base.memberships) == 1
    membership = knowledge_base.memberships[0]
    assert membership.user_id == owner_user_id
    assert membership.role == KnowledgeBaseRole.OWNER.value
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


async def test_knowledge_base_access_queries_are_membership_scoped() -> None:
    session = AsyncMock(spec=AsyncSession)
    user_id = uuid4()
    knowledge_base_id = uuid4()
    knowledge_base = KnowledgeBase(id=knowledge_base_id, name="Private")
    row_result = MagicMock()
    row_result.one_or_none.return_value = (
        knowledge_base,
        KnowledgeBaseRole.EDITOR.value,
    )
    row_result.all.return_value = [(knowledge_base, KnowledgeBaseRole.EDITOR.value)]
    session.execute.return_value = row_result
    repository = KnowledgeBaseRepository(session)

    retrieved = await repository.get_for_user(
        knowledge_base_id,
        user_id=user_id,
    )
    upload_target = await repository.get_upload_target_for_user(
        knowledge_base_id,
        user_id=user_id,
    )
    listed = await repository.list_for_user(
        user_id=user_id,
        limit=20,
        offset=10,
    )

    assert retrieved == (knowledge_base, KnowledgeBaseRole.EDITOR)
    assert upload_target == (knowledge_base, KnowledgeBaseRole.EDITOR)
    assert listed == [(knowledge_base, KnowledgeBaseRole.EDITOR)]
    for call in session.execute.await_args_list:
        rendered = _postgresql_sql(call.args[0])
        assert "JOIN knowledge_base_memberships" in rendered
        assert "knowledge_base_memberships.user_id =" in rendered
    assert "FOR UPDATE" not in _postgresql_sql(session.execute.await_args_list[0].args[0])
    assert "FOR UPDATE" in _postgresql_sql(session.execute.await_args_list[1].args[0])
    list_statement = session.execute.await_args_list[-1].args[0]
    assert list_statement._limit_clause.value == 20
    assert list_statement._offset_clause.value == 10


async def test_document_access_queries_join_membership_scope() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one_or_none.return_value = None
    result.all.return_value = []
    session.execute.return_value = result
    repository = DocumentRepository(session)
    user_id = uuid4()

    assert await repository.get_for_user(uuid4(), user_id=user_id) is None
    assert (
        await repository.list_for_knowledge_base_for_user(
            uuid4(),
            user_id=user_id,
            limit=25,
            offset=5,
        )
        == []
    )

    for call in session.execute.await_args_list:
        rendered = _postgresql_sql(call.args[0])
        assert "FROM documents JOIN knowledge_bases" in rendered
        assert "JOIN knowledge_base_memberships" in rendered
        assert "knowledge_bases.id = documents.knowledge_base_id" in rendered
        assert "knowledge_base_memberships.knowledge_base_id = knowledge_bases.id" in rendered
        assert "knowledge_base_memberships.user_id =" in rendered


async def test_job_access_and_retry_queries_join_membership_scope() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one_or_none.return_value = None
    session.execute.return_value = result
    repository = IngestionJobRepository(session)
    user_id = uuid4()

    assert await repository.get_for_user(uuid4(), user_id=user_id) is None
    assert (
        await repository.get_retry_target_for_user(
            uuid4(),
            user_id=user_id,
        )
        is None
    )

    read_statement = session.execute.await_args_list[0].args[0]
    retry_statement = session.execute.await_args_list[1].args[0]
    for statement in (read_statement, retry_statement):
        rendered = _postgresql_sql(statement)
        assert "FROM ingestion_jobs JOIN documents" in rendered
        assert "JOIN knowledge_bases" in rendered
        assert "JOIN knowledge_base_memberships" in rendered
        assert "knowledge_bases.id = documents.knowledge_base_id" in rendered
        assert "knowledge_base_memberships.knowledge_base_id = knowledge_bases.id" in rendered
        assert "knowledge_base_memberships.user_id =" in rendered
    assert "FOR UPDATE" not in _postgresql_sql(read_statement)
    assert "FOR UPDATE" in _postgresql_sql(retry_statement)


async def test_legacy_claim_counts_and_claims_only_unowned_knowledge_bases() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = 2
    scalar_result = MagicMock()
    scalar_result.all.return_value = [uuid4(), uuid4()]
    session.scalars.return_value = scalar_result
    repository = KnowledgeBaseMembershipRepository(session)

    count = await repository.count_unowned_internal()
    claimed = await repository.claim_unowned_internal(owner_user_id=uuid4())

    assert count == 2
    assert claimed == 2
    count_sql = _postgresql_sql(session.scalar.await_args.args[0])
    claim_sql = _postgresql_sql(session.scalars.await_args.args[0])
    assert "FROM knowledge_bases" in count_sql
    assert "NOT (EXISTS" in count_sql
    assert "INSERT INTO knowledge_base_memberships" in claim_sql
    assert "NOT (EXISTS" in claim_sql
    assert "ON CONFLICT (knowledge_base_id, user_id) DO NOTHING" in claim_sql
    lock_sql = _postgresql_sql(session.execute.await_args.args[0])
    assert "pg_advisory_xact_lock" in lock_sql
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


async def test_document_digest_query_scopes_to_knowledge_base_and_user() -> None:
    session = AsyncMock(spec=AsyncSession)
    result_rows = MagicMock()
    result_rows.one_or_none.return_value = None
    session.execute.return_value = result_rows
    knowledge_base_id = uuid4()
    user_id = uuid4()

    result = await DocumentRepository(session).get_by_digest_for_user(
        knowledge_base_id=knowledge_base_id,
        sha256="a" * 64,
        user_id=user_id,
    )

    assert result is None
    rendered = _postgresql_sql(session.execute.await_args.args[0])
    assert "documents.knowledge_base_id" in rendered
    assert "documents.sha256" in rendered
    assert "JOIN knowledge_bases" in rendered
    assert "JOIN knowledge_base_memberships" in rendered
    assert "knowledge_base_memberships.user_id" in rendered


async def test_document_list_uses_bounded_deterministic_query() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    knowledge_base_id = uuid4()

    result = await DocumentRepository(session).list_for_knowledge_base_internal(
        knowledge_base_id,
        limit=25,
        offset=5,
    )

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = str(statement)
    assert "ORDER BY documents.created_at ASC, documents.id ASC" in rendered
    assert statement._limit_clause.value == 25
    assert statement._offset_clause.value == 5


async def test_document_and_job_add_flush_without_commit() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    document = Document(
        knowledge_base_id=uuid4(),
        original_filename="file.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256="a" * 64,
        storage_key="kb/file.txt",
    )
    job = IngestionJob(document=document)

    await DocumentRepository(session).add_authorized_upload(document)
    await IngestionJobRepository(session).add_for_authorized_upload(job)

    assert session.add.call_count == 2
    assert session.flush.await_count == 2
    session.commit.assert_not_awaited()


async def test_document_chunk_list_uses_deterministic_chunk_order() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    document_id = uuid4()

    result = await DocumentChunkRepository(session).list_for_document_internal(document_id)

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = str(statement)
    assert "document_chunks.document_id" in rendered
    assert "ORDER BY document_chunks.chunk_index ASC" in rendered


async def test_document_chunk_list_applies_and_validates_a_positive_limit() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    repository = DocumentChunkRepository(session)

    await repository.list_for_document_internal(uuid4(), limit=50)

    statement = session.scalars.await_args.args[0]
    assert statement._limit_clause.value == 50

    with pytest.raises(ValueError, match="positive"):
        await repository.list_for_document_internal(uuid4(), limit=0)


async def test_document_chunk_replace_deletes_and_flushes_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add_all = MagicMock()
    document_id = uuid4()
    chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=0,
            normalized_text="First chunk",
            token_count=2,
        ),
        DocumentChunk(
            document_id=document_id,
            chunk_index=1,
            normalized_text="Second chunk",
            token_count=2,
        ),
    ]

    await DocumentChunkRepository(session).replace_for_document_internal(document_id, chunks)

    delete_statement = session.execute.await_args.args[0]
    assert "DELETE FROM document_chunks" in str(delete_statement)
    assert "document_chunks.document_id" in str(delete_statement)
    session.add_all.assert_called_once_with(chunks)
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


async def test_document_chunk_replace_rejects_mismatched_document_ids() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add_all = MagicMock()
    document_id = uuid4()
    mismatched_chunk = DocumentChunk(
        document_id=uuid4(),
        chunk_index=0,
        normalized_text="Wrong document",
        token_count=2,
    )

    with pytest.raises(ValueError, match="document_id"):
        await DocumentChunkRepository(session).replace_for_document_internal(
            document_id,
            [mismatched_chunk],
        )

    session.execute.assert_not_awaited()
    session.add_all.assert_not_called()
    session.flush.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_claim_next_uses_due_retry_eligibility_and_skip_locked() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).claim_next_internal(
        worker_id="worker-1",
        claimed_at=claimed_at,
        lease_expires_at=claimed_at + timedelta(minutes=5),
    )

    assert result is None
    statement = session.scalar.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.attempt_count < ingestion_jobs.max_attempts" in rendered
    assert "ingestion_jobs.next_retry_at IS NULL" in rendered
    assert "ingestion_jobs.next_retry_at <=" in rendered
    assert (
        "ORDER BY coalesce(ingestion_jobs.next_retry_at, ingestion_jobs.created_at) ASC" in rendered
    )
    assert "FOR UPDATE SKIP LOCKED" in rendered
    assert statement._limit_clause.value == 1


async def test_claim_next_updates_job_and_document_without_committing() -> None:
    session = AsyncMock(spec=AsyncSession)
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)
    document = Document(
        knowledge_base_id=uuid4(),
        original_filename="file.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256="a" * 64,
        storage_key="kb/file.txt",
        status=DocumentStatus.PENDING.value,
    )
    job = IngestionJob(
        document=document,
        status=IngestionJobStatus.PENDING.value,
        attempt_count=1,
        max_attempts=3,
        progress_percent=40,
        next_retry_at=claimed_at,
        error_code="TRANSIENT",
        safe_error_message="Try again.",
    )
    session.scalar.return_value = job

    claimed = await IngestionJobRepository(session).claim_next_internal(
        worker_id="worker-1",
        claimed_at=claimed_at,
        lease_expires_at=claimed_at + timedelta(minutes=5),
    )

    assert claimed is job
    assert job.status == IngestionJobStatus.PROCESSING.value
    assert job.attempt_count == 2
    assert job.progress_percent == 0
    assert job.claimed_by == "worker-1"
    assert job.claimed_at == claimed_at
    assert job.lease_expires_at == claimed_at + timedelta(minutes=5)
    assert job.next_retry_at is None
    assert job.error_code is None
    assert job.safe_error_message is None
    assert job.started_at == claimed_at
    assert job.finished_at is None
    assert document.status == DocumentStatus.PROCESSING.value
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("worker_id", "lease_delta"),
    [(" ", timedelta(minutes=5)), ("worker-1", timedelta(0))],
)
async def test_claim_next_rejects_invalid_lease_inputs(
    worker_id: str,
    lease_delta: timedelta,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    claimed_at = datetime(2026, 7, 28, 12, tzinfo=UTC)

    with pytest.raises(ValueError):
        await IngestionJobRepository(session).claim_next_internal(
            worker_id=worker_id,
            claimed_at=claimed_at,
            lease_expires_at=claimed_at + lease_delta,
        )

    session.scalar.assert_not_awaited()


async def test_expired_lease_query_is_bounded_ordered_and_skip_locked() -> None:
    session = AsyncMock(spec=AsyncSession)
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result
    now = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).lock_expired_leases_internal(
        now=now,
        limit=10,
    )

    assert result == []
    statement = session.scalars.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.lease_expires_at IS NOT NULL" in rendered
    assert "ingestion_jobs.lease_expires_at <=" in rendered
    assert "ORDER BY ingestion_jobs.lease_expires_at ASC, ingestion_jobs.id ASC" in rendered
    assert "FOR UPDATE SKIP LOCKED" in rendered
    assert statement._limit_clause.value == 10


async def test_expired_lease_query_rejects_a_nonpositive_limit() -> None:
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(ValueError, match="positive"):
        await IngestionJobRepository(session).lock_expired_leases_internal(
            now=datetime(2026, 7, 28, 12, tzinfo=UTC),
            limit=0,
        )

    session.scalars.assert_not_awaited()


@pytest.mark.parametrize("for_update", [False, True])
async def test_owned_processing_query_fences_status_worker_and_expiry(
    for_update: bool,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    now = datetime(2026, 7, 28, 12, tzinfo=UTC)

    result = await IngestionJobRepository(session).get_owned_processing_internal(
        uuid4(),
        worker_id="worker-1",
        now=now,
        for_update=for_update,
    )

    assert result is None
    statement = session.scalar.await_args.args[0]
    rendered = _postgresql_sql(statement)
    assert "ingestion_jobs.status =" in rendered
    assert "ingestion_jobs.claimed_by =" in rendered
    assert "ingestion_jobs.lease_expires_at >" in rendered
    assert ("FOR UPDATE" in rendered) is for_update
