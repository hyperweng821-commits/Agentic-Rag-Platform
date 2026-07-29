"""Live ASGI and PostgreSQL coverage for the AF-2S1 security boundary."""

import asyncio
import hashlib
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from argon2 import PasswordHasher as RawArgonPasswordHasher
from argon2.low_level import Type
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import delete, event, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.dependencies import get_db_session
from app.core.config import get_settings
from app.db.models import (
    Document,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)
from app.ingestion.storage import AsyncReadable, LocalFileStorage, StoredFile
from app.main import create_app
from app.security import Argon2idPasswordHasher, hash_token

pytestmark = pytest.mark.integration

PASSWORD = "".join(("live-", "owner-passphrase"))
WRONG_PASSWORD = "".join(("wrong-", "owner-passphrase"))
PRIVATE_CACHE_CONTROL = "private, no-store"


@dataclass(frozen=True, slots=True)
class LiveSecurityData:
    owner_id: UUID
    editor_id: UUID
    viewer_id: UUID
    outsider_id: UUID
    inactive_id: UUID
    malformed_id: UUID
    owner_password_hash: str
    malformed_password_hash: str
    shared_knowledge_base_id: UUID
    outsider_knowledge_base_id: UUID
    legacy_knowledge_base_id: UUID
    shared_document_id: UUID
    outsider_document_id: UUID
    legacy_document_id: UUID
    shared_job_id: UUID
    outsider_job_id: UUID
    legacy_job_id: UUID
    owner_session_token: str
    owner_csrf_token: str
    second_session_csrf_token: str
    viewer_session_token: str
    viewer_csrf_token: str
    expired_session_token: str
    revoked_session_token: str
    inactive_session_token: str
    duplicate_content: bytes


def _user(*, email: str, password_hash: str, active: bool = True) -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash=password_hash,
        is_active=active,
    )


def _session(
    *,
    user_id: UUID,
    session_token: str,
    csrf_token: str,
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> UserSession:
    return UserSession(
        id=uuid4(),
        user_id=user_id,
        token_sha256=hash_token(session_token),
        csrf_token_sha256=hash_token(csrf_token),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _set_session_cookies(
    client: AsyncClient,
    *,
    session_token: str,
    csrf_token: str | None,
) -> None:
    client.cookies.set("agentforge_session", session_token, path="/api/v1")
    if csrf_token is not None:
        client.cookies.set("agentforge_csrf", csrf_token, path="/")


def _assert_private(response: Response) -> None:
    assert response.headers["cache-control"] == PRIVATE_CACHE_CONTROL


def _assert_no_authentication_secrets(
    response: Response,
    data: LiveSecurityData,
) -> None:
    for secret in (
        PASSWORD,
        WRONG_PASSWORD,
        data.owner_password_hash,
        data.malformed_password_hash,
        data.owner_session_token,
        data.owner_csrf_token,
        hash_token(data.owner_session_token),
        hash_token(data.owner_csrf_token),
        "SELECT ",
        "sqlalchemy",
        "asyncpg",
        "Traceback",
        "Exception",
    ):
        assert secret not in response.text


@pytest.fixture
def live_application(
    postgres_sessions: async_sessionmaker[AsyncSession],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[FastAPI]:
    """Create the real app, overriding only its session provider."""
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    application = create_app()

    async def override_database_session() -> AsyncIterator[AsyncSession]:
        async with postgres_sessions() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db_session] = override_database_session
    try:
        yield application
    finally:
        application.dependency_overrides.clear()
        application.state.password_work_limiter.shutdown()
        get_settings.cache_clear()


@pytest.fixture
async def live_client(live_application: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=live_application, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def live_security_data(
    postgres_sessions: async_sessionmaker[AsyncSession],
) -> LiveSecurityData:
    hasher = Argon2idPasswordHasher()
    password_hash = await asyncio.to_thread(hasher.hash_password, PASSWORD)
    malformed_password_hash = "".join(("$argon2id$", "malformed-live-hash"))
    owner = _user(email="owner@example.com", password_hash=password_hash)
    editor = _user(email="editor@example.com", password_hash=password_hash)
    viewer = _user(email="viewer@example.com", password_hash=password_hash)
    outsider = _user(email="outsider@example.com", password_hash=password_hash)
    inactive = _user(
        email="inactive@example.com",
        password_hash=password_hash,
        active=False,
    )
    malformed = _user(
        email="malformed@example.com",
        password_hash=malformed_password_hash,
    )

    shared = KnowledgeBase(id=uuid4(), name="Shared private")
    outsider_knowledge_base = KnowledgeBase(id=uuid4(), name="Outsider private")
    legacy = KnowledgeBase(id=uuid4(), name="Legacy unowned")
    shared_document = Document(
        id=uuid4(),
        knowledge_base_id=shared.id,
        original_filename="failed.txt",
        media_type="text/plain",
        size_bytes=6,
        sha256="a" * 64,
        storage_key=f"{shared.id}/failed.txt",
        status="failed",
    )
    shared_job = IngestionJob(
        id=uuid4(),
        document=shared_document,
        status=IngestionJobStatus.FAILED.value,
        attempt_count=1,
        max_attempts=3,
        progress_percent=0,
    )
    duplicate_content = b"principal scoped duplicate"
    outsider_document = Document(
        id=uuid4(),
        knowledge_base_id=outsider_knowledge_base.id,
        original_filename="outsider.txt",
        media_type="text/plain",
        size_bytes=len(duplicate_content),
        sha256=hashlib.sha256(duplicate_content).hexdigest(),
        storage_key=f"{outsider_knowledge_base.id}/outsider.txt",
        status="failed",
    )
    outsider_job = IngestionJob(
        id=uuid4(),
        document=outsider_document,
        status=IngestionJobStatus.FAILED.value,
        attempt_count=1,
        max_attempts=3,
    )
    legacy_document = Document(
        id=uuid4(),
        knowledge_base_id=legacy.id,
        original_filename="legacy.txt",
        media_type="text/plain",
        size_bytes=6,
        sha256="b" * 64,
        storage_key=f"{legacy.id}/legacy.txt",
        status="failed",
    )
    legacy_job = IngestionJob(
        id=uuid4(),
        document=legacy_document,
        status=IngestionJobStatus.FAILED.value,
        attempt_count=1,
        max_attempts=3,
    )

    now = datetime.now(UTC)
    owner_session_token = "o" * 43
    owner_csrf_token = "c" * 43
    second_session_token = "p" * 43
    second_session_csrf_token = "d" * 43
    viewer_session_token = "v" * 43
    viewer_csrf_token = "w" * 43
    expired_session_token = "e" * 43
    revoked_session_token = "r" * 43
    inactive_session_token = "i" * 43
    sessions = [
        _session(
            user_id=owner.id,
            session_token=owner_session_token,
            csrf_token=owner_csrf_token,
            expires_at=now + timedelta(hours=1),
        ),
        _session(
            user_id=owner.id,
            session_token=second_session_token,
            csrf_token=second_session_csrf_token,
            expires_at=now + timedelta(hours=1),
        ),
        _session(
            user_id=viewer.id,
            session_token=viewer_session_token,
            csrf_token=viewer_csrf_token,
            expires_at=now + timedelta(hours=1),
        ),
        _session(
            user_id=owner.id,
            session_token=expired_session_token,
            csrf_token="f" * 43,
            expires_at=now - timedelta(minutes=1),
        ),
        _session(
            user_id=owner.id,
            session_token=revoked_session_token,
            csrf_token="s" * 43,
            expires_at=now + timedelta(hours=1),
            revoked_at=now - timedelta(minutes=1),
        ),
        _session(
            user_id=inactive.id,
            session_token=inactive_session_token,
            csrf_token="j" * 43,
            expires_at=now + timedelta(hours=1),
        ),
    ]

    async with postgres_sessions() as session, session.begin():
        session.add_all(
            [
                owner,
                editor,
                viewer,
                outsider,
                inactive,
                malformed,
                shared,
                outsider_knowledge_base,
                legacy,
                KnowledgeBaseMembership(
                    knowledge_base_id=shared.id,
                    user_id=owner.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=shared.id,
                    user_id=editor.id,
                    role=KnowledgeBaseRole.EDITOR.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=shared.id,
                    user_id=viewer.id,
                    role=KnowledgeBaseRole.VIEWER.value,
                ),
                KnowledgeBaseMembership(
                    knowledge_base_id=outsider_knowledge_base.id,
                    user_id=outsider.id,
                    role=KnowledgeBaseRole.OWNER.value,
                ),
                shared_document,
                shared_job,
                outsider_document,
                outsider_job,
                legacy_document,
                legacy_job,
                *sessions,
            ]
        )

    return LiveSecurityData(
        owner_id=owner.id,
        editor_id=editor.id,
        viewer_id=viewer.id,
        outsider_id=outsider.id,
        inactive_id=inactive.id,
        malformed_id=malformed.id,
        owner_password_hash=password_hash,
        malformed_password_hash=malformed_password_hash,
        shared_knowledge_base_id=shared.id,
        outsider_knowledge_base_id=outsider_knowledge_base.id,
        legacy_knowledge_base_id=legacy.id,
        shared_document_id=shared_document.id,
        outsider_document_id=outsider_document.id,
        legacy_document_id=legacy_document.id,
        shared_job_id=shared_job.id,
        outsider_job_id=outsider_job.id,
        legacy_job_id=legacy_job.id,
        owner_session_token=owner_session_token,
        owner_csrf_token=owner_csrf_token,
        second_session_csrf_token=second_session_csrf_token,
        viewer_session_token=viewer_session_token,
        viewer_csrf_token=viewer_csrf_token,
        expired_session_token=expired_session_token,
        revoked_session_token=revoked_session_token,
        inactive_session_token=inactive_session_token,
        duplicate_content=duplicate_content,
    )


async def test_live_login_me_logout_and_revocation(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
) -> None:
    async with postgres_sessions() as session:
        sessions_before = await session.scalar(select(func.count()).select_from(UserSession))

    login = await live_client.post(
        "/api/v1/auth/login",
        json={"email": " OWNER@EXAMPLE.COM ", "password": PASSWORD},
    )

    assert login.status_code == 200
    assert login.json() == {
        "id": str(live_security_data.owner_id),
        "email": "owner@example.com",
    }
    assert "session_id" not in login.json()
    _assert_private(login)
    _assert_no_authentication_secrets(login, live_security_data)

    me = await live_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json() == login.json()
    assert set(me.json()) == {"id", "email"}
    _assert_private(me)
    _assert_no_authentication_secrets(me, live_security_data)

    csrf_token = live_client.cookies["agentforge_csrf"]
    logout = await live_client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 204
    _assert_private(logout)

    async with postgres_sessions() as session:
        sessions_after = await session.scalar(select(func.count()).select_from(UserSession))
        revoked_count = await session.scalar(
            select(func.count()).select_from(UserSession).where(UserSession.revoked_at.is_not(None))
        )
    assert sessions_after == cast(int, sessions_before) + 1
    assert cast(int, revoked_count) >= 2

    after_logout = await live_client.get("/api/v1/auth/me")
    assert after_logout.status_code == 401
    assert after_logout.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    _assert_private(after_logout)


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("unknown@example.com", PASSWORD),
        ("owner@example.com", WRONG_PASSWORD),
        ("inactive@example.com", PASSWORD),
        ("malformed@example.com", PASSWORD),
    ],
    ids=["unknown-email", "wrong-password", "inactive-user", "malformed-hash"],
)
async def test_live_login_failures_are_generic_and_do_not_mutate_credentials(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
    email: str,
    password: str,
) -> None:
    async with postgres_sessions() as session:
        sessions_before = await session.scalar(select(func.count()).select_from(UserSession))
        hashes_before = dict((await session.execute(select(User.id, User.password_hash))).all())

    response = await live_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["message"] == "Authentication is required."
    assert email not in response.text
    assert password not in response.text
    _assert_private(response)
    _assert_no_authentication_secrets(response, live_security_data)

    async with postgres_sessions() as session:
        sessions_after = await session.scalar(select(func.count()).select_from(UserSession))
        hashes_after = dict((await session.execute(select(User.id, User.password_hash))).all())
    assert sessions_after == sessions_before
    assert hashes_after == hashes_before


@pytest.mark.parametrize(
    "session_case",
    ["missing", "malformed", "expired", "revoked", "inactive-user"],
)
async def test_live_unusable_sessions_share_one_unauthorized_contract(
    live_client: AsyncClient,
    live_security_data: LiveSecurityData,
    session_case: str,
) -> None:
    session_tokens = {
        "malformed": "malformed",
        "expired": live_security_data.expired_session_token,
        "revoked": live_security_data.revoked_session_token,
        "inactive-user": live_security_data.inactive_session_token,
    }
    if session_case != "missing":
        _set_session_cookies(
            live_client,
            session_token=session_tokens[session_case],
            csrf_token=None,
        )

    response = await live_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["message"] == "Authentication is required."
    _assert_private(response)
    _assert_no_authentication_secrets(response, live_security_data)


@pytest.mark.parametrize(
    "csrf_case",
    ["missing-header", "missing-cookie", "mismatch", "different-session"],
)
async def test_live_logout_enforces_session_bound_csrf(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
    csrf_case: str,
) -> None:
    csrf_cookie: str | None = live_security_data.owner_csrf_token
    csrf_header: str | None = live_security_data.owner_csrf_token
    if csrf_case == "missing-header":
        csrf_header = None
    elif csrf_case == "missing-cookie":
        csrf_cookie = None
    elif csrf_case == "mismatch":
        csrf_header = "z" * 43
    else:
        csrf_cookie = live_security_data.second_session_csrf_token
        csrf_header = live_security_data.second_session_csrf_token
    _set_session_cookies(
        live_client,
        session_token=live_security_data.owner_session_token,
        csrf_token=csrf_cookie,
    )
    headers = {} if csrf_header is None else {"X-CSRF-Token": csrf_header}

    response = await live_client.post("/api/v1/auth/logout", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"
    _assert_private(response)
    async with postgres_sessions() as session:
        owner_session = await session.scalar(
            select(UserSession).where(
                UserSession.token_sha256 == hash_token(live_security_data.owner_session_token)
            )
        )
    assert owner_session is not None
    assert owner_session.revoked_at is None


async def test_live_viewer_reads_but_cannot_upload_or_retry(
    live_client: AsyncClient,
    live_security_data: LiveSecurityData,
) -> None:
    _set_session_cookies(
        live_client,
        session_token=live_security_data.viewer_session_token,
        csrf_token=live_security_data.viewer_csrf_token,
    )
    reads = [
        await live_client.get(
            f"/api/v1/knowledge-bases/{live_security_data.shared_knowledge_base_id}"
        ),
        await live_client.get(f"/api/v1/documents/{live_security_data.shared_document_id}"),
        await live_client.get(f"/api/v1/ingestion-jobs/{live_security_data.shared_job_id}"),
    ]
    for response in reads:
        assert response.status_code == 200
        _assert_private(response)

    upload = await live_client.post(
        (f"/api/v1/knowledge-bases/{live_security_data.shared_knowledge_base_id}/documents"),
        files={"file": ("viewer.txt", b"viewer private", "text/plain")},
        headers={"X-CSRF-Token": live_security_data.viewer_csrf_token},
    )
    retry = await live_client.post(
        f"/api/v1/ingestion-jobs/{live_security_data.shared_job_id}/retry",
        headers={"X-CSRF-Token": live_security_data.viewer_csrf_token},
    )
    for response in (upload, retry):
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"
        _assert_private(response)
        _assert_no_authentication_secrets(response, live_security_data)


async def test_live_cross_user_and_legacy_resources_are_indistinguishable_404s(
    live_client: AsyncClient,
    live_application: FastAPI,
    live_security_data: LiveSecurityData,
) -> None:
    _set_session_cookies(
        live_client,
        session_token=live_security_data.owner_session_token,
        csrf_token=live_security_data.owner_csrf_token,
    )
    paths = [
        f"/api/v1/knowledge-bases/{live_security_data.outsider_knowledge_base_id}",
        f"/api/v1/documents/{live_security_data.outsider_document_id}",
        f"/api/v1/ingestion-jobs/{live_security_data.outsider_job_id}",
        f"/api/v1/knowledge-bases/{live_security_data.legacy_knowledge_base_id}",
        f"/api/v1/documents/{live_security_data.legacy_document_id}",
        f"/api/v1/ingestion-jobs/{live_security_data.legacy_job_id}",
    ]
    for path in paths:
        response = await live_client.get(path)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
        _assert_private(response)
        _assert_no_authentication_secrets(response, live_security_data)

    unauthenticated_transport = ASGITransport(
        app=live_application,
        raise_app_exceptions=False,
    )
    async with AsyncClient(
        transport=unauthenticated_transport,
        base_url="http://test",
    ) as unauthenticated:
        response = await unauthenticated.get("/api/v1/knowledge-bases")
    assert response.status_code == 401
    _assert_private(response)


async def test_live_valid_csrf_writes_and_repository_lock_boundaries(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
) -> None:
    _set_session_cookies(
        live_client,
        session_token=live_security_data.owner_session_token,
        csrf_token=live_security_data.owner_csrf_token,
    )
    engine = cast(AsyncEngine, postgres_sessions.kw["bind"])
    statements: list[str] = []

    def record_statement(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record_statement)
    try:
        created = await live_client.post(
            "/api/v1/knowledge-bases",
            json={"name": "Created with CSRF", "description": None},
            headers={"X-CSRF-Token": live_security_data.owner_csrf_token},
        )
        first_upload = await live_client.post(
            (f"/api/v1/knowledge-bases/{live_security_data.shared_knowledge_base_id}/documents"),
            files={
                "file": (
                    "principal.txt",
                    live_security_data.duplicate_content,
                    "text/plain",
                )
            },
            headers={"X-CSRF-Token": live_security_data.owner_csrf_token},
        )
        duplicate_upload = await live_client.post(
            (f"/api/v1/knowledge-bases/{live_security_data.shared_knowledge_base_id}/documents"),
            files={
                "file": (
                    "principal.txt",
                    live_security_data.duplicate_content,
                    "text/plain",
                )
            },
            headers={"X-CSRF-Token": live_security_data.owner_csrf_token},
        )
        retried = await live_client.post(
            f"/api/v1/ingestion-jobs/{live_security_data.shared_job_id}/retry",
            headers={"X-CSRF-Token": live_security_data.owner_csrf_token},
        )
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record_statement)

    assert created.status_code == 201
    assert first_upload.status_code == 201
    assert duplicate_upload.status_code == 200
    assert retried.status_code == 200
    for response in (created, first_upload, duplicate_upload, retried):
        _assert_private(response)
        _assert_no_authentication_secrets(response, live_security_data)
    uploaded_id = first_upload.json()["document"]["id"]
    assert uploaded_id != str(live_security_data.outsider_document_id)
    assert duplicate_upload.json()["document"]["id"] == uploaded_id
    assert duplicate_upload.json()["duplicate"] is True

    locked_membership_reads = [
        statement
        for statement in statements
        if "knowledge_base_memberships" in statement and "FOR UPDATE" in statement
    ]
    assert len(locked_membership_reads) >= 4
    assert any(
        "FROM ingestion_jobs JOIN documents" in statement
        and "JOIN knowledge_base_memberships" in statement
        and "FOR UPDATE" in statement
        for statement in statements
    )

    async with postgres_sessions() as session:
        created_membership = await session.scalar(
            select(KnowledgeBaseMembership).where(
                KnowledgeBaseMembership.knowledge_base_id == UUID(created.json()["id"]),
                KnowledgeBaseMembership.user_id == live_security_data.owner_id,
            )
        )
        shared_job = await session.get(IngestionJob, live_security_data.shared_job_id)
    assert created_membership is not None
    assert created_membership.role == KnowledgeBaseRole.OWNER.value
    assert shared_job is not None
    assert shared_job.status == IngestionJobStatus.PENDING.value


async def test_live_upload_rechecks_membership_after_real_storage(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_session_cookies(
        live_client,
        session_token=live_security_data.owner_session_token,
        csrf_token=live_security_data.owner_csrf_token,
    )
    stored = asyncio.Event()
    resume = asyncio.Event()
    real_store = LocalFileStorage.store

    async def coordinated_store(
        storage: LocalFileStorage,
        source: AsyncReadable,
        *,
        storage_key: str,
        max_bytes: int,
    ) -> StoredFile:
        result = await real_store(
            storage,
            source,
            storage_key=storage_key,
            max_bytes=max_bytes,
        )
        stored.set()
        await resume.wait()
        return result

    monkeypatch.setattr(LocalFileStorage, "store", coordinated_store)
    content = b"membership revoked during storage"
    request_task = asyncio.create_task(
        live_client.post(
            (f"/api/v1/knowledge-bases/{live_security_data.shared_knowledge_base_id}/documents"),
            files={"file": ("revoked.txt", content, "text/plain")},
            headers={"X-CSRF-Token": live_security_data.owner_csrf_token},
        )
    )
    try:
        await asyncio.wait_for(stored.wait(), timeout=5)
        async with postgres_sessions() as session, session.begin():
            await session.execute(
                delete(KnowledgeBaseMembership).where(
                    KnowledgeBaseMembership.knowledge_base_id
                    == live_security_data.shared_knowledge_base_id,
                    KnowledgeBaseMembership.user_id == live_security_data.owner_id,
                )
            )
    finally:
        resume.set()
    response = await asyncio.wait_for(request_task, timeout=5)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    _assert_private(response)
    async with postgres_sessions() as session:
        stored_document_count = await session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.sha256 == hashlib.sha256(content).hexdigest())
        )
    assert stored_document_count == 0
    upload_root = tmp_path / "uploads"
    assert not any(path.is_file() for path in upload_root.rglob("*"))


async def test_live_argon_rehash_upgrade_current_hash_stability_and_failed_no_rewrite(
    live_client: AsyncClient,
    postgres_sessions: async_sessionmaker[AsyncSession],
    live_security_data: LiveSecurityData,
) -> None:
    outdated_hash = await asyncio.to_thread(
        RawArgonPasswordHasher(
            time_cost=1,
            memory_cost=8 * 1024,
            parallelism=1,
            type=Type.ID,
        ).hash,
        PASSWORD,
    )
    async with postgres_sessions() as session, session.begin():
        owner = await session.get(User, live_security_data.owner_id)
        assert owner is not None
        owner.password_hash = outdated_hash

    upgraded_login = await live_client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert upgraded_login.status_code == 200
    async with postgres_sessions() as session:
        upgraded_hash = await session.scalar(
            select(User.password_hash).where(User.id == live_security_data.owner_id)
        )
    assert upgraded_hash is not None
    assert upgraded_hash != outdated_hash
    hasher = Argon2idPasswordHasher()
    assert hasher.verify_password(PASSWORD, upgraded_hash)
    assert hasher.needs_rehash(upgraded_hash) is False

    failed_login = await live_client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": WRONG_PASSWORD},
    )
    assert failed_login.status_code == 401
    live_client.cookies.clear()
    current_login = await live_client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert current_login.status_code == 200
    async with postgres_sessions() as session:
        final_hash = await session.scalar(
            select(User.password_hash).where(User.id == live_security_data.owner_id)
        )
    assert final_hash == upgraded_hash
