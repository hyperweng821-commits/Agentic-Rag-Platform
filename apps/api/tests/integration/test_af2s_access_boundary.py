"""Opt-in PostgreSQL tests for the AF-2S knowledge access boundary."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.cli.security import OperatorCommandError, SecurityOperatorService
from app.db.models import (
    Document,
    IngestionJob,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)
from app.db.repositories import (
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseMembershipRepository,
    KnowledgeBaseRepository,
)
from app.ingestion.storage import LocalFileStorage
from app.security import Principal
from app.services.knowledge_intake import KnowledgeIntakeService

pytestmark = pytest.mark.integration


def _run_revision(
    connection: Connection,
    revision: str,
    direction: Literal["upgrade", "downgrade"],
) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    revision_script = scripts.get_revision(revision)
    migration = cast(Callable[[], None], getattr(revision_script.module, direction))
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        migration()


def _upgrade_through_af2b(connection: Connection) -> None:
    for revision in ("20260727_0001", "20260728_0002", "20260728_0003"):
        _run_revision(connection, revision, "upgrade")


def _user(email: str) -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash="".join(("$argon2id$", "integration-test-hash")),
        is_active=True,
    )


async def test_membership_scoped_joins_preserve_roles_and_cross_user_isolation(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    owner = _user("owner@example.com")
    editor = _user("editor@example.com")
    viewer = _user("viewer@example.com")
    unrelated = _user("unrelated@example.com")
    private_knowledge_base = KnowledgeBase(id=uuid4(), name="Private")
    other_knowledge_base = KnowledgeBase(id=uuid4(), name="Other user")
    unowned_knowledge_base = KnowledgeBase(id=uuid4(), name="Legacy unowned")
    private_document = Document(
        id=uuid4(),
        knowledge_base_id=private_knowledge_base.id,
        original_filename="private.txt",
        media_type="text/plain",
        size_bytes=7,
        sha256="a" * 64,
        storage_key=f"{private_knowledge_base.id}/private.txt",
    )
    private_job = IngestionJob(id=uuid4(), document=private_document)
    other_document = Document(
        id=uuid4(),
        knowledge_base_id=other_knowledge_base.id,
        original_filename="other.txt",
        media_type="text/plain",
        size_bytes=5,
        sha256="b" * 64,
        storage_key=f"{other_knowledge_base.id}/other.txt",
    )
    other_job = IngestionJob(id=uuid4(), document=other_document)
    unowned_document = Document(
        id=uuid4(),
        knowledge_base_id=unowned_knowledge_base.id,
        original_filename="legacy.txt",
        media_type="text/plain",
        size_bytes=6,
        sha256="c" * 64,
        storage_key=f"{unowned_knowledge_base.id}/legacy.txt",
    )
    unowned_job = IngestionJob(id=uuid4(), document=unowned_document)

    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                owner,
                editor,
                viewer,
                unrelated,
                private_knowledge_base,
                other_knowledge_base,
                unowned_knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=private_knowledge_base.id,
                    user_id=owner.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=private_knowledge_base.id,
                    user_id=editor.id,
                    role=KnowledgeBaseRole.EDITOR.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=private_knowledge_base.id,
                    user_id=viewer.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=other_knowledge_base.id,
                    user_id=unrelated.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                private_document,
                private_job,
                other_document,
                other_job,
                unowned_document,
                unowned_job,
            ]
        )

    expected_roles = {
        owner.id: KnowledgeBaseRole.OWNER,
        editor.id: KnowledgeBaseRole.EDITOR,
        viewer.id: KnowledgeBaseRole.VIEWER,
    }
    async with postgres_sessions() as session:
        knowledge_bases = KnowledgeBaseRepository(session)
        documents = DocumentRepository(session)
        jobs = IngestionJobRepository(session)

        for user_id, expected_role in expected_roles.items():
            knowledge_access = await knowledge_bases.get_for_user(
                private_knowledge_base.id,
                user_id=user_id,
            )
            document_access = await documents.get_for_user(
                private_document.id,
                user_id=user_id,
            )
            job_access = await jobs.get_for_user(
                private_job.id,
                user_id=user_id,
            )
            retry_access = await jobs.get_retry_target_for_user(
                private_job.id,
                user_id=user_id,
                for_update=False,
            )

            assert knowledge_access is not None
            assert knowledge_access[0].id == private_knowledge_base.id
            assert knowledge_access[1] == expected_role
            assert document_access is not None
            assert document_access[0].id == private_document.id
            assert document_access[1] == expected_role
            assert job_access is not None
            assert job_access[0].id == private_job.id
            assert job_access[1] == expected_role
            assert retry_access is not None
            assert retry_access[0].id == private_job.id
            assert retry_access[1] == expected_role
            assert (
                await knowledge_bases.get_for_user(
                    other_knowledge_base.id,
                    user_id=user_id,
                )
                is None
            )
            assert (
                await documents.get_for_user(
                    other_document.id,
                    user_id=user_id,
                )
                is None
            )
            assert await jobs.get_for_user(other_job.id, user_id=user_id) is None

        assert (
            await knowledge_bases.get_for_user(
                private_knowledge_base.id,
                user_id=unrelated.id,
            )
            is None
        )
        assert (
            await documents.get_for_user(
                private_document.id,
                user_id=unrelated.id,
            )
            is None
        )
        assert await jobs.get_for_user(private_job.id, user_id=unrelated.id) is None
        assert (
            await jobs.get_retry_target_for_user(
                private_job.id,
                user_id=unrelated.id,
                for_update=False,
            )
            is None
        )

        for user_id in (*expected_roles, unrelated.id):
            assert (
                await knowledge_bases.get_for_user(
                    unowned_knowledge_base.id,
                    user_id=user_id,
                )
                is None
            )
            assert (
                await documents.get_for_user(
                    unowned_document.id,
                    user_id=user_id,
                )
                is None
            )
            assert await jobs.get_for_user(unowned_job.id, user_id=user_id) is None

        owner_knowledge_bases = await knowledge_bases.list_for_user(
            user_id=owner.id,
            limit=20,
            offset=0,
        )
        unrelated_knowledge_bases = await knowledge_bases.list_for_user(
            user_id=unrelated.id,
            limit=20,
            offset=0,
        )
        owner_documents = await documents.list_for_knowledge_base_for_user(
            private_knowledge_base.id,
            user_id=owner.id,
            limit=20,
            offset=0,
        )
        unrelated_documents = await documents.list_for_knowledge_base_for_user(
            private_knowledge_base.id,
            user_id=unrelated.id,
            limit=20,
            offset=0,
        )

    assert [(knowledge_base.id, role) for knowledge_base, role in owner_knowledge_bases] == [
        (private_knowledge_base.id, KnowledgeBaseRole.OWNER)
    ]
    assert [(knowledge_base.id, role) for knowledge_base, role in unrelated_knowledge_bases] == [
        (other_knowledge_base.id, KnowledgeBaseRole.OWNER)
    ]
    assert [(document.id, role) for document, role in owner_documents] == [
        (private_document.id, KnowledgeBaseRole.OWNER)
    ]
    assert unrelated_documents == []


async def test_postgresql_rejects_duplicate_knowledge_base_memberships(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = _user("member@example.com")
    knowledge_base = KnowledgeBase(id=uuid4(), name="Private")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                user,
                knowledge_base,
                KnowledgeBaseMembership(
                    knowledge_base_id=knowledge_base.id,
                    user_id=user.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
            ]
        )

    async with postgres_sessions() as session:
        session.add(
            KnowledgeBaseMembership(
                knowledge_base_id=knowledge_base.id,
                user_id=user.id,
                role=KnowledgeBaseRole.VIEWER.value,
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

    async with postgres_sessions() as session:
        memberships = list(
            (
                await session.scalars(
                    select(KnowledgeBaseMembership).where(
                        KnowledgeBaseMembership.knowledge_base_id == knowledge_base.id,
                        KnowledgeBaseMembership.user_id == user.id,
                    )
                )
            ).all()
        )

    assert len(memberships) == 1
    assert memberships[0].role == KnowledgeBaseRole.OWNER.value


async def test_knowledge_base_creation_atomically_adds_owner_or_rolls_back(
    postgres_sessions: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    owner = _user("creator@example.com")
    async with postgres_sessions() as session, session.begin():
        session.add(owner)

    principal = Principal(
        user_id=owner.id,
        email=owner.email,
        session_id=uuid4(),
    )
    async with postgres_sessions() as session:
        service = KnowledgeIntakeService(
            session,
            LocalFileStorage(tmp_path),
            max_upload_size_bytes=1024,
        )
        knowledge_base = await service.create_knowledge_base(
            principal,
            name="Owned at creation",
            description=None,
        )
        knowledge_base_id = knowledge_base.id

    async with postgres_sessions() as session:
        membership = await session.scalar(
            select(KnowledgeBaseMembership).where(
                KnowledgeBaseMembership.knowledge_base_id == knowledge_base_id,
                KnowledgeBaseMembership.user_id == owner.id,
            )
        )

    assert membership is not None
    assert membership.role == KnowledgeBaseRole.OWNER.value

    missing_user_principal = Principal(
        user_id=uuid4(),
        email="missing@example.com",
        session_id=uuid4(),
    )
    async with postgres_sessions() as session:
        service = KnowledgeIntakeService(
            session,
            LocalFileStorage(tmp_path),
            max_upload_size_bytes=1024,
        )
        with pytest.raises(IntegrityError):
            await service.create_knowledge_base(
                missing_user_principal,
                name="Must roll back",
                description=None,
            )

    async with postgres_sessions() as session:
        rolled_back_count = await session.scalar(
            select(func.count())
            .select_from(KnowledgeBase)
            .where(KnowledgeBase.name == "Must roll back")
        )

    assert rolled_back_count == 0


async def test_operator_claim_is_idempotent_and_preserves_owned_knowledge_bases(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> None:
    claimant = _user("claimant@example.com")
    existing_owner = _user("existing-owner@example.com")
    editor = _user("editor-member@example.com")
    viewer = _user("viewer-member@example.com")
    owned = KnowledgeBase(id=uuid4(), name="Already owned")
    editor_only = KnowledgeBase(id=uuid4(), name="Editor only")
    viewer_only = KnowledgeBase(id=uuid4(), name="Viewer only")
    first_unowned = KnowledgeBase(id=uuid4(), name="Legacy one")
    second_unowned = KnowledgeBase(id=uuid4(), name="Legacy two")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                claimant,
                existing_owner,
                editor,
                viewer,
                owned,
                editor_only,
                viewer_only,
                first_unowned,
                second_unowned,
                KnowledgeBaseMembership(
                    knowledge_base_id=owned.id,
                    user_id=existing_owner.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=editor_only.id,
                    user_id=editor.id,
                    role=KnowledgeBaseRole.EDITOR.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=viewer_only.id,
                    user_id=viewer.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
            ]
        )

    async with postgres_sessions() as session:
        service = SecurityOperatorService(session)
        dry_run_count = await service.claim_legacy_knowledge_bases(
            owner_email=" CLAIMANT@EXAMPLE.COM ",
            dry_run=True,
        )
        first_claim_count = await service.claim_legacy_knowledge_bases(
            owner_email="claimant@example.com",
            dry_run=False,
        )
        second_claim_count = await service.claim_legacy_knowledge_bases(
            owner_email="claimant@example.com",
            dry_run=False,
        )

    assert dry_run_count == 2
    assert first_claim_count == 2
    assert second_claim_count == 0

    async with postgres_sessions() as session:
        memberships = list(
            (
                await session.scalars(
                    select(KnowledgeBaseMembership).order_by(
                        KnowledgeBaseMembership.knowledge_base_id,
                        KnowledgeBaseMembership.user_id,
                    )
                )
            ).all()
        )

    by_knowledge_base = {
        membership.knowledge_base_id: (membership.user_id, membership.role)
        for membership in memberships
    }
    assert by_knowledge_base == {
        owned.id: (existing_owner.id, KnowledgeBaseRole.OWNER.value),
        editor_only.id: (editor.id, KnowledgeBaseRole.EDITOR.value),
        viewer_only.id: (viewer.id, KnowledgeBaseRole.VIEWER.value),
        first_unowned.id: (claimant.id, KnowledgeBaseRole.OWNER.value),
        second_unowned.id: (claimant.id, KnowledgeBaseRole.OWNER.value),
    }


@pytest.mark.parametrize("dry_run", [False, True], ids=["write", "dry-run"])
async def test_operator_claim_rejects_inactive_target_without_membership_write(
    postgres_sessions: async_sessionmaker[AsyncSession],
    dry_run: bool,
) -> None:
    inactive = _user("inactive-claimant@example.com")
    inactive.is_active = False
    unowned = KnowledgeBase(id=uuid4(), name="Remain unowned")
    async with postgres_sessions() as session, session.begin():
        session.add_all([inactive, unowned])

    async with postgres_sessions() as session:
        with pytest.raises(OperatorCommandError, match="inactive"):
            await SecurityOperatorService(session).claim_legacy_knowledge_bases(
                owner_email=inactive.email,
                dry_run=dry_run,
            )

    async with postgres_sessions() as session:
        membership_count = await session.scalar(
            select(func.count())
            .select_from(KnowledgeBaseMembership)
            .where(KnowledgeBaseMembership.knowledge_base_id == unowned.id)
        )

    assert membership_count == 0


async def test_concurrent_operator_claims_serialize_and_choose_one_owner(
    postgres_sessions: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_owner = _user("first-claimant@example.com")
    second_owner = _user("second-claimant@example.com")
    editor = _user("existing-editor@example.com")
    viewer = _user("existing-viewer@example.com")
    unowned = [
        KnowledgeBase(id=uuid4(), name="Concurrent legacy one"),
        KnowledgeBase(id=uuid4(), name="Concurrent legacy two"),
    ]
    editor_only = KnowledgeBase(id=uuid4(), name="Concurrent editor only")
    viewer_only = KnowledgeBase(id=uuid4(), name="Concurrent viewer only")
    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                first_owner,
                second_owner,
                editor,
                viewer,
                *unowned,
                editor_only,
                viewer_only,
                KnowledgeBaseMembership(
                    knowledge_base_id=editor_only.id,
                    user_id=editor.id,
                    role=KnowledgeBaseRole.EDITOR.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=viewer_only.id,
                    user_id=viewer.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
            ]
        )

    first_claimed = asyncio.Event()
    release_first = asyncio.Event()
    second_entered = asyncio.Event()
    second_pid: dict[str, int] = {}
    real_claim = KnowledgeBaseMembershipRepository.claim_unowned_internal

    async def coordinated_claim(
        repository: KnowledgeBaseMembershipRepository,
        *,
        owner_user_id: UUID,
    ) -> int:
        if owner_user_id == first_owner.id:
            claimed = await real_claim(repository, owner_user_id=owner_user_id)
            first_claimed.set()
            await release_first.wait()
            return claimed
        pid = await repository._session.scalar(text("SELECT pg_backend_pid()"))
        assert pid is not None
        second_pid["value"] = int(pid)
        second_entered.set()
        return await real_claim(repository, owner_user_id=owner_user_id)

    monkeypatch.setattr(
        KnowledgeBaseMembershipRepository,
        "claim_unowned_internal",
        coordinated_claim,
    )

    async def claim(owner: User) -> int:
        async with postgres_sessions() as session:
            return await SecurityOperatorService(session).claim_legacy_knowledge_bases(
                owner_email=owner.email,
                dry_run=False,
            )

    first_task = asyncio.create_task(claim(first_owner))
    second_task: asyncio.Task[int] | None = None
    try:
        await asyncio.wait_for(first_claimed.wait(), timeout=5)
        second_task = asyncio.create_task(claim(second_owner))
        await asyncio.wait_for(second_entered.wait(), timeout=5)

        async def second_is_waiting_on_advisory_lock() -> bool:
            async with postgres_sessions() as observer:
                for _ in range(200):
                    waiting = await observer.scalar(
                        text(
                            "SELECT EXISTS ("
                            "SELECT 1 FROM pg_locks "
                            "WHERE pid = :pid AND locktype = 'advisory' AND NOT granted"
                            ")"
                        ),
                        {"pid": second_pid["value"]},
                    )
                    if waiting:
                        return True
                    await asyncio.sleep(0.01)
            return False

        assert await asyncio.wait_for(
            second_is_waiting_on_advisory_lock(),
            timeout=5,
        )
        assert second_task.done() is False
    finally:
        release_first.set()
        tasks = [first_task] + ([] if second_task is None else [second_task])
        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=5,
        )

    assert second_task is not None
    first_count = first_task.result()
    second_count = second_task.result()
    assert (first_count, second_count) == (len(unowned), 0)

    async with postgres_sessions() as session:
        memberships = list(
            (
                await session.scalars(
                    select(KnowledgeBaseMembership).where(
                        KnowledgeBaseMembership.knowledge_base_id.in_(
                            [item.id for item in unowned] + [editor_only.id, viewer_only.id]
                        )
                    )
                )
            ).all()
        )

    by_knowledge_base: dict[UUID, list[tuple[UUID, str]]] = {}
    for membership in memberships:
        by_knowledge_base.setdefault(membership.knowledge_base_id, []).append(
            (membership.user_id, membership.role)
        )
    for knowledge_base in unowned:
        assert by_knowledge_base[knowledge_base.id] == [
            (first_owner.id, KnowledgeBaseRole.OWNER.value)
        ]
    assert by_knowledge_base[editor_only.id] == [(editor.id, KnowledgeBaseRole.EDITOR.value)]
    assert by_knowledge_base[viewer_only.id] == [(viewer.id, KnowledgeBaseRole.VIEWER.value)]


def _seed_legacy_data(
    connection: Connection,
    *,
    knowledge_base_id: UUID,
    document_id: UUID,
    job_id: UUID,
    chunk_id: UUID,
) -> None:
    connection.execute(
        text(
            "INSERT INTO knowledge_bases (id, name, description) VALUES (:id, :name, :description)"
        ),
        {
            "id": knowledge_base_id,
            "name": "Legacy knowledge",
            "description": "Preserve this",
        },
    )
    connection.execute(
        text(
            "INSERT INTO documents "
            "(id, knowledge_base_id, original_filename, media_type, size_bytes, "
            "sha256, storage_key, status) "
            "VALUES (:id, :knowledge_base_id, :filename, :media_type, :size_bytes, "
            ":sha256, :storage_key, :status)"
        ),
        {
            "id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "filename": "legacy.txt",
            "media_type": "text/plain",
            "size_bytes": 14,
            "sha256": "d" * 64,
            "storage_key": f"{knowledge_base_id}/legacy.txt",
            "status": "completed",
        },
    )
    connection.execute(
        text(
            "INSERT INTO ingestion_jobs "
            "(id, document_id, status, attempt_count, max_attempts, progress_percent) "
            "VALUES (:id, :document_id, :status, :attempt_count, "
            ":max_attempts, :progress_percent)"
        ),
        {
            "id": job_id,
            "document_id": document_id,
            "status": "completed",
            "attempt_count": 1,
            "max_attempts": 3,
            "progress_percent": 100,
        },
    )
    connection.execute(
        text(
            "INSERT INTO document_chunks "
            "(id, document_id, chunk_index, normalized_text, token_count, "
            "content_sha256, start_offset, end_offset, page_start, page_end) "
            "VALUES (:id, :document_id, :chunk_index, :normalized_text, :token_count, "
            ":content_sha256, :start_offset, :end_offset, :page_start, :page_end)"
        ),
        {
            "id": chunk_id,
            "document_id": document_id,
            "chunk_index": 0,
            "normalized_text": "Legacy content",
            "token_count": 2,
            "content_sha256": "e" * 64,
            "start_offset": 0,
            "end_offset": 14,
            "page_start": 1,
            "page_end": 1,
        },
    )


def _legacy_snapshot(connection: Connection) -> tuple[tuple[object, ...], ...]:
    return (
        tuple(
            connection.execute(
                text("SELECT id, name, description FROM knowledge_bases ORDER BY id")
            ).one()
        ),
        tuple(
            connection.execute(
                text(
                    "SELECT id, knowledge_base_id, original_filename, media_type, "
                    "size_bytes, sha256, storage_key, status "
                    "FROM documents ORDER BY id"
                )
            ).one()
        ),
        tuple(
            connection.execute(
                text(
                    "SELECT id, document_id, status, attempt_count, max_attempts, "
                    "progress_percent FROM ingestion_jobs ORDER BY id"
                )
            ).one()
        ),
        tuple(
            connection.execute(
                text(
                    "SELECT id, document_id, chunk_index, normalized_text, token_count, "
                    "content_sha256, start_offset, end_offset, page_start, page_end "
                    "FROM document_chunks ORDER BY id"
                )
            ).one()
        ),
    )


def _access_boundary_counts(connection: Connection) -> tuple[int, int, int]:
    return (
        cast(int, connection.execute(text("SELECT count(*) FROM users")).scalar_one()),
        cast(
            int,
            connection.execute(text("SELECT count(*) FROM user_sessions")).scalar_one(),
        ),
        cast(
            int,
            connection.execute(
                text("SELECT count(*) FROM knowledge_base_memberships")
            ).scalar_one(),
        ),
    )


def _seed_access_boundary_data(
    connection: Connection,
    *,
    user_id: UUID,
    session_id: UUID,
    knowledge_base_id: UUID,
) -> None:
    connection.execute(
        User.__table__.insert(),
        {
            "id": user_id,
            "email": "downgrade-owner@example.com",
            "password_hash": "$argon2id$destructive-downgrade-test",
            "is_active": True,
        },
    )
    connection.execute(
        UserSession.__table__.insert(),
        {
            "id": session_id,
            "user_id": user_id,
            "token_sha256": "a" * 64,
            "csrf_token_sha256": "b" * 64,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        },
    )
    connection.execute(
        KnowledgeBaseMembership.__table__.insert(),
        {
            "knowledge_base_id": knowledge_base_id,
            "user_id": user_id,
            "role": KnowledgeBaseRole.OWNER.value,
        },
    )


def _access_boundary_tables(connection: Connection) -> set[str]:
    return {
        table_name
        for table_name in inspect(connection).get_table_names()
        if table_name in {"users", "user_sessions", "knowledge_base_memberships"}
    }


async def test_af2s_migration_round_trip_preserves_legacy_data_without_claiming_it(
    postgres_migration_engine: AsyncEngine,
) -> None:
    knowledge_base_id = uuid4()
    document_id = uuid4()
    job_id = uuid4()
    chunk_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()

    async with postgres_migration_engine.begin() as connection:
        await connection.run_sync(_upgrade_through_af2b)
        await connection.run_sync(
            lambda sync_connection: _seed_legacy_data(
                sync_connection,
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                job_id=job_id,
                chunk_id=chunk_id,
            )
        )
        expected_snapshot = await connection.run_sync(_legacy_snapshot)

        await connection.run_sync(
            lambda sync_connection: _run_revision(
                sync_connection,
                "20260729_0004",
                "upgrade",
            )
        )
        assert await connection.run_sync(_legacy_snapshot) == expected_snapshot
        assert await connection.run_sync(_access_boundary_counts) == (0, 0, 0)
        assert await connection.run_sync(_access_boundary_tables) == {
            "users",
            "user_sessions",
            "knowledge_base_memberships",
        }
        await connection.run_sync(
            lambda sync_connection: _seed_access_boundary_data(
                sync_connection,
                user_id=user_id,
                session_id=session_id,
                knowledge_base_id=knowledge_base_id,
            )
        )
        assert await connection.run_sync(_access_boundary_counts) == (1, 1, 1)

        await connection.run_sync(
            lambda sync_connection: _run_revision(
                sync_connection,
                "20260729_0004",
                "downgrade",
            )
        )
        assert await connection.run_sync(_legacy_snapshot) == expected_snapshot
        assert await connection.run_sync(_access_boundary_tables) == set()

        await connection.run_sync(
            lambda sync_connection: _run_revision(
                sync_connection,
                "20260729_0004",
                "upgrade",
            )
        )
        assert await connection.run_sync(_legacy_snapshot) == expected_snapshot
        assert await connection.run_sync(_access_boundary_counts) == (0, 0, 0)
        assert await connection.run_sync(_access_boundary_tables) == {
            "users",
            "user_sessions",
            "knowledge_base_memberships",
        }
