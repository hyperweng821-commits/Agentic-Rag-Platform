"""AF-2S1 password, opaque-session, CSRF, principal, and capability tests."""

import asyncio
import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from argon2 import PasswordHasher as RawArgonPasswordHasher
from argon2.low_level import Type
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeBaseRole, User, UserSession
from app.db.repositories import AuthenticationUserSnapshot
from app.security import authorization
from app.security.authentication import (
    AuthenticationError,
    AuthenticationService,
    CsrfError,
    hash_token,
)
from app.security.authorization import (
    AuthorizationError,
    Capability,
    capabilities_for,
    require_capability,
)
from app.security.passwords import (
    MAX_PASSWORD_LENGTH,
    Argon2idPasswordHasher,
    PasswordWorkLimiter,
)
from app.security.principal import Principal, normalize_email

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
SESSION_TOKEN = "s" * 43
CSRF_TOKEN = "c" * 43


class TransactionContext(AbstractAsyncContextManager[None]):
    """Minimal transaction boundary for repository-free service tests."""

    def __init__(self, session: "FakeSession") -> None:
        self._session = session

    async def __aenter__(self) -> None:
        assert self._session.active_transaction is False
        self._session.active_transaction = True
        return None

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.active_transaction = False
        return None


class FakeSession:
    """Expose only the transaction operation owned by AuthenticationService."""

    def __init__(self) -> None:
        self.active_transaction = False

    def begin(self) -> TransactionContext:
        return TransactionContext(self)

    def in_transaction(self) -> bool:
        return self.active_transaction


class ImmediatePasswordWorkLimiter:
    """Run deterministic fake password operations without creating threads."""

    async def run(
        self,
        operation: Callable[..., object],
        *args: object,
    ) -> object:
        return operation(*args)


class StubPasswordHasher:
    """Deterministic injected password verifier."""

    def __init__(
        self,
        *,
        valid: bool = True,
        rehash: bool = False,
        session: FakeSession | None = None,
    ) -> None:
        self.valid = valid
        self.rehash = rehash
        self.session = session
        self.verifications: list[tuple[str, str | None]] = []
        self.hashes: list[str] = []
        self.verify_transaction_states: list[bool] = []
        self.hash_transaction_states: list[bool] = []

    def hash_password(self, password: str) -> str:
        self.hashes.append(password)
        if self.session is not None:
            self.hash_transaction_states.append(self.session.in_transaction())
        return f"$argon2id$replacement:{password}"

    def verify_password(self, password: str, password_hash: str | None) -> bool:
        self.verifications.append((password, password_hash))
        if self.session is not None:
            self.verify_transaction_states.append(self.session.in_transaction())
        return self.valid and password_hash is not None

    def needs_rehash(self, password_hash: str) -> bool:
        return self.rehash


def _tokens() -> Iterator[str]:
    yield SESSION_TOKEN
    yield CSRF_TOKEN


def _user(*, active: bool = True) -> User:
    encoded_hash = "".join(("$argon2id$", "encoded"))
    return User(
        id=uuid4(),
        email="owner@example.com",
        password_hash=encoded_hash,
        is_active=active,
        created_at=NOW,
        updated_at=NOW,
    )


def _user_session(
    user: User,
    *,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> UserSession:
    return UserSession(
        id=uuid4(),
        user_id=user.id,
        user=user,
        token_sha256=hash_token(SESSION_TOKEN),
        csrf_token_sha256=hash_token(CSRF_TOKEN),
        expires_at=expires_at or NOW + timedelta(hours=1),
        revoked_at=revoked_at,
        created_at=NOW,
        updated_at=NOW,
    )


def _service(
    *,
    password_hasher: StubPasswordHasher | None = None,
    fake_session: FakeSession | None = None,
) -> tuple[AuthenticationService, AsyncMock, AsyncMock]:
    token_values = _tokens()
    session = fake_session or FakeSession()
    service = AuthenticationService(
        cast(AsyncSession, session),
        session_ttl=timedelta(hours=2),
        password_work_limiter=cast(
            PasswordWorkLimiter,
            ImmediatePasswordWorkLimiter(),
        ),
        password_hasher=password_hasher or StubPasswordHasher(),
        clock=lambda: NOW,
        token_factory=lambda: next(token_values),
    )
    users = AsyncMock()
    sessions = AsyncMock()
    service._users = users
    service._sessions = sessions
    return service, users, sessions


def _snapshot(user: User) -> AuthenticationUserSnapshot:
    return AuthenticationUserSnapshot(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        password_hash=user.password_hash,
    )


def test_argon2id_hashes_verify_and_use_fresh_salts() -> None:
    hasher = Argon2idPasswordHasher()
    plain_text = "".join(("correct horse", " battery staple"))

    first_hash = hasher.hash_password(plain_text)
    second_hash = hasher.hash_password(plain_text)

    assert first_hash.startswith("$argon2id$")
    assert second_hash.startswith("$argon2id$")
    assert first_hash != second_hash
    assert hasher.verify_password(plain_text, first_hash) is True
    assert hasher.verify_password("incorrect", first_hash) is False
    assert hasher.verify_password(plain_text, "not-an-argon-hash") is False
    assert hasher.verify_password(plain_text, None) is False
    assert hasher.needs_rehash(first_hash) is False
    assert hasher.needs_rehash("not-an-argon-hash") is False


def test_argon2id_rejects_empty_password_for_persistence() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Argon2idPasswordHasher().hash_password("")


def test_argon2id_detects_deliberately_outdated_lower_cost_hash() -> None:
    plain_text = "".join(("upgrade-", "passphrase"))
    outdated = RawArgonPasswordHasher(
        time_cost=1,
        memory_cost=8 * 1024,
        parallelism=1,
        type=Type.ID,
    ).hash(plain_text)

    assert Argon2idPasswordHasher().needs_rehash(outdated) is True


def test_argon2id_enforces_shared_password_maximum() -> None:
    over_limit = "p" * (MAX_PASSWORD_LENGTH + 1)
    hasher = Argon2idPasswordHasher()

    with pytest.raises(ValueError, match=str(MAX_PASSWORD_LENGTH)):
        hasher.hash_password(over_limit)
    assert hasher.verify_password(over_limit, None) is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" Owner@Example.COM ", "owner@example.com"),
        ("ümlaut@EXAMPLE.COM", "ümlaut@example.com"),
    ],
)
def test_email_normalization(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "x" * 321])
def test_invalid_normalized_email_is_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_email(raw)


def test_principal_is_a_model_independent_value_object() -> None:
    principal = Principal(user_id=uuid4(), email="owner@example.com", session_id=uuid4())

    assert isinstance(principal.user_id, UUID)
    with pytest.raises(AttributeError):
        principal.email = "changed@example.com"  # type: ignore[misc]


async def test_login_normalizes_email_and_persists_only_token_digests() -> None:
    hasher = StubPasswordHasher()
    service, users, sessions = _service(password_hasher=hasher)
    user = _user()
    users.get_for_authentication_by_email.return_value = _snapshot(user)
    users.get_locked_for_authentication.return_value = user
    assigned_session_id = uuid4()

    async def add(user_session: UserSession) -> None:
        user_session.id = assigned_session_id

    sessions.add_for_authentication.side_effect = add
    plain_text = "".join(("local-", "passphrase"))

    credentials = await service.login(email=" OWNER@EXAMPLE.COM ", password=plain_text)

    users.get_for_authentication_by_email.assert_awaited_once_with("owner@example.com")
    users.get_locked_for_authentication.assert_awaited_once_with(user.id)
    assert hasher.verifications == [(plain_text, user.password_hash)]
    stored_session = sessions.add_for_authentication.await_args.args[0]
    assert isinstance(stored_session, UserSession)
    assert stored_session.token_sha256 == hash_token(SESSION_TOKEN)
    assert stored_session.csrf_token_sha256 == hash_token(CSRF_TOKEN)
    assert SESSION_TOKEN not in stored_session.__dict__.values()
    assert CSRF_TOKEN not in stored_session.__dict__.values()
    assert credentials.session_token == SESSION_TOKEN
    assert credentials.csrf_token == CSRF_TOKEN
    assert credentials.expires_at == NOW + timedelta(hours=2)
    assert credentials.principal == Principal(user.id, user.email, assigned_session_id)
    users.update_password_hash_for_authentication.assert_not_awaited()


@pytest.mark.parametrize(
    ("user", "password_valid"),
    [
        (None, False),
        (_user(active=False), True),
        (_user(), False),
    ],
    ids=["unknown-email", "inactive-user", "invalid-password"],
)
async def test_login_failures_use_one_generic_error(
    user: User | None,
    password_valid: bool,
) -> None:
    hasher = StubPasswordHasher(valid=password_valid)
    service, users, sessions = _service(password_hasher=hasher)
    users.get_for_authentication_by_email.return_value = None if user is None else _snapshot(user)
    candidate = "".join(("candidate", "-passphrase"))

    with pytest.raises(AuthenticationError) as exc_info:
        await service.login(email="person@example.com", password=candidate)

    assert exc_info.value.public_message == AuthenticationError.message
    assert hasher.verifications == [(candidate, None if user is None else user.password_hash)]
    users.get_locked_for_authentication.assert_not_awaited()
    users.update_password_hash_for_authentication.assert_not_awaited()
    sessions.add_for_authentication.assert_not_awaited()


async def test_password_verification_and_rehash_run_without_an_active_transaction() -> None:
    fake_session = FakeSession()
    hasher = StubPasswordHasher(rehash=True, session=fake_session)
    service, users, sessions = _service(
        password_hasher=hasher,
        fake_session=fake_session,
    )
    user = _user()
    users.get_for_authentication_by_email.return_value = _snapshot(user)
    users.get_locked_for_authentication.return_value = user
    assigned_session_id = uuid4()

    async def add(user_session: UserSession) -> None:
        user_session.id = assigned_session_id

    sessions.add_for_authentication.side_effect = add
    password = "".join(("rehash-", "passphrase"))

    credentials = await service.login(email=user.email, password=password)

    assert credentials.principal.session_id == assigned_session_id
    assert hasher.verify_transaction_states == [False]
    assert hasher.hash_transaction_states == [False]
    users.update_password_hash_for_authentication.assert_awaited_once_with(
        user,
        password_hash=f"$argon2id$replacement:{password}",
    )
    assert fake_session.in_transaction() is False


@pytest.mark.parametrize(
    "changed_state",
    ["deleted", "inactive", "password-changed"],
)
async def test_login_fails_closed_when_locked_user_state_changes(
    changed_state: str,
) -> None:
    service, users, sessions = _service(password_hasher=StubPasswordHasher())
    observed_user = _user()
    users.get_for_authentication_by_email.return_value = _snapshot(observed_user)
    locked_user: User | None
    if changed_state == "deleted":
        locked_user = None
    else:
        locked_user = _user(active=changed_state != "inactive")
        locked_user.id = observed_user.id
        locked_user.email = observed_user.email
        if changed_state == "password-changed":
            locked_user.password_hash = "".join(("$argon2id$", "concurrent-change"))
    users.get_locked_for_authentication.return_value = locked_user

    with pytest.raises(AuthenticationError) as exc_info:
        await service.login(
            email=observed_user.email,
            password="".join(("valid-", "passphrase")),
        )

    assert exc_info.value.public_message == AuthenticationError.message
    users.update_password_hash_for_authentication.assert_not_awaited()
    sessions.add_for_authentication.assert_not_awaited()


async def test_malformed_argon_hash_fails_closed_without_session_or_rewrite() -> None:
    hasher = Argon2idPasswordHasher()
    token_values = _tokens()
    service = AuthenticationService(
        cast(AsyncSession, FakeSession()),
        session_ttl=timedelta(hours=2),
        password_work_limiter=cast(
            PasswordWorkLimiter,
            ImmediatePasswordWorkLimiter(),
        ),
        password_hasher=hasher,
        clock=lambda: NOW,
        token_factory=lambda: next(token_values),
    )
    malformed_user = _user()
    malformed_user.password_hash = "".join(("$argon2id$", "malformed"))
    users = AsyncMock()
    sessions = AsyncMock()
    users.get_for_authentication_by_email.return_value = _snapshot(malformed_user)
    service._users = users
    service._sessions = sessions

    with pytest.raises(AuthenticationError):
        await service.login(
            email=malformed_user.email,
            password="".join(("candidate-", "passphrase")),
        )

    users.get_locked_for_authentication.assert_not_awaited()
    users.update_password_hash_for_authentication.assert_not_awaited()
    sessions.add_for_authentication.assert_not_awaited()


@pytest.mark.parametrize("outdated", [False, True], ids=["current", "outdated"])
async def test_successful_login_rewrites_only_outdated_argon_hash(outdated: bool) -> None:
    password = "".join(("argon-", "upgrade-passphrase"))
    hasher = Argon2idPasswordHasher()
    password_hash = (
        RawArgonPasswordHasher(
            time_cost=1,
            memory_cost=8 * 1024,
            parallelism=1,
            type=Type.ID,
        ).hash(password)
        if outdated
        else hasher.hash_password(password)
    )
    user = _user()
    user.password_hash = password_hash
    token_values = _tokens()
    service = AuthenticationService(
        cast(AsyncSession, FakeSession()),
        session_ttl=timedelta(hours=1),
        password_work_limiter=cast(
            PasswordWorkLimiter,
            ImmediatePasswordWorkLimiter(),
        ),
        password_hasher=hasher,
        clock=lambda: NOW,
        token_factory=lambda: next(token_values),
    )
    users = AsyncMock()
    sessions = AsyncMock()
    users.get_for_authentication_by_email.return_value = _snapshot(user)
    users.get_locked_for_authentication.return_value = user

    async def add(user_session: UserSession) -> None:
        user_session.id = uuid4()

    sessions.add_for_authentication.side_effect = add
    service._users = users
    service._sessions = sessions

    await service.login(email=user.email, password=password)

    if outdated:
        replacement = users.update_password_hash_for_authentication.await_args.kwargs[
            "password_hash"
        ]
        assert replacement != password_hash
        assert hasher.verify_password(password, replacement) is True
        assert hasher.needs_rehash(replacement) is False
    else:
        users.update_password_hash_for_authentication.assert_not_awaited()


async def test_authentication_accepts_shared_maximum_and_rejects_over_limit_early() -> None:
    maximum = "p" * MAX_PASSWORD_LENGTH
    hasher = StubPasswordHasher()
    service, users, sessions = _service(password_hasher=hasher)
    user = _user()
    users.get_for_authentication_by_email.return_value = _snapshot(user)
    users.get_locked_for_authentication.return_value = user

    async def add(user_session: UserSession) -> None:
        user_session.id = uuid4()

    sessions.add_for_authentication.side_effect = add
    await service.login(email=user.email, password=maximum)
    assert hasher.verifications == [(maximum, user.password_hash)]

    over_limit = "q" * (MAX_PASSWORD_LENGTH + 1)
    second_hasher = StubPasswordHasher()
    second_service, second_users, second_sessions = _service(password_hasher=second_hasher)
    with pytest.raises(AuthenticationError) as exc_info:
        await second_service.login(email=user.email, password=over_limit)

    assert exc_info.value.public_message == AuthenticationError.message
    assert over_limit not in str(exc_info.value)
    assert second_hasher.verifications == []
    second_users.get_for_authentication_by_email.assert_not_awaited()
    second_sessions.add_for_authentication.assert_not_awaited()


async def test_shared_password_limiter_bounds_concurrent_unknown_user_verification() -> None:
    class BlockingHasher:
        def __init__(self) -> None:
            self.active = 0
            self.maximum = 0
            self.lock = threading.Lock()
            self.limit_reached = threading.Event()
            self.release = threading.Event()

        def hash_password(self, password: str) -> str:
            raise AssertionError("Unknown-user login must not rehash.")

        def verify_password(self, password: str, password_hash: str | None) -> bool:
            assert password_hash is None
            with self.lock:
                self.active += 1
                self.maximum = max(self.maximum, self.active)
                if self.active == 2:
                    self.limit_reached.set()
            try:
                assert self.release.wait(timeout=5)
                return False
            finally:
                with self.lock:
                    self.active -= 1

        def needs_rehash(self, password_hash: str) -> bool:
            return False

    limiter = PasswordWorkLimiter(2)
    hasher = BlockingHasher()
    services: list[AuthenticationService] = []
    for _ in range(6):
        service = AuthenticationService(
            cast(AsyncSession, FakeSession()),
            session_ttl=timedelta(hours=1),
            password_work_limiter=limiter,
            password_hasher=hasher,
            clock=lambda: NOW,
        )
        users = AsyncMock()
        users.get_for_authentication_by_email.return_value = None
        service._users = users
        service._sessions = AsyncMock()
        services.append(service)

    tasks = [
        asyncio.create_task(
            service.login(
                email=f"unknown-{index}@example.com",
                password="".join(("candidate-", "passphrase")),
            )
        )
        for index, service in enumerate(services)
    ]
    try:
        reached = await asyncio.wait_for(
            asyncio.to_thread(hasher.limit_reached.wait, 2),
            timeout=3,
        )
        assert reached is True
        assert hasher.maximum == 2
        assert sum(not task.done() for task in tasks) == len(tasks)
    finally:
        hasher.release.set()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        limiter.shutdown()

    assert hasher.maximum == 2
    assert all(isinstance(result, AuthenticationError) for result in results)


async def test_active_session_constructs_principal_and_touches_last_seen() -> None:
    service, _, sessions = _service()
    user = _user()
    user_session = _user_session(user)
    sessions.get_active_for_authentication_by_token_sha256.return_value = user_session

    principal = await service.authenticate_session(SESSION_TOKEN)

    assert principal == Principal(user.id, user.email, user_session.id)
    sessions.get_active_for_authentication_by_token_sha256.assert_awaited_once_with(
        hash_token(SESSION_TOKEN),
        now=NOW,
    )
    sessions.touch_for_authentication.assert_awaited_once_with(user_session, seen_at=NOW)


@pytest.mark.parametrize(
    "session_token",
    [None, "", "short", "contains forbidden spaces" * 2],
)
async def test_malformed_session_token_fails_without_database_lookup(
    session_token: str | None,
) -> None:
    service, _, sessions = _service()

    with pytest.raises(AuthenticationError):
        await service.authenticate_session(session_token)

    sessions.get_active_for_authentication_by_token_sha256.assert_not_awaited()


@pytest.mark.parametrize(
    "user_session",
    [
        None,
        _user_session(_user(), expires_at=NOW),
        _user_session(_user(), revoked_at=NOW - timedelta(minutes=1)),
        _user_session(_user(active=False)),
    ],
    ids=["unknown", "expired", "revoked", "inactive-user"],
)
async def test_unusable_session_fails_closed(user_session: UserSession | None) -> None:
    service, _, sessions = _service()
    sessions.get_active_for_authentication_by_token_sha256.return_value = user_session

    with pytest.raises(AuthenticationError):
        await service.authenticate_session(SESSION_TOKEN)

    sessions.touch_for_authentication.assert_not_awaited()


async def test_logout_revokes_current_session() -> None:
    service, _, sessions = _service()
    user_session = _user_session(_user())
    sessions.get_active_for_authentication_by_token_sha256.return_value = user_session

    await service.revoke_session(SESSION_TOKEN)

    sessions.revoke_for_authentication.assert_awaited_once_with(
        user_session,
        revoked_at=NOW,
    )


async def test_matching_csrf_token_succeeds() -> None:
    service, _, sessions = _service()
    user_session = _user_session(_user())
    sessions.get_active_for_authentication_by_token_sha256.return_value = user_session

    await service.validate_csrf(
        session_token=SESSION_TOKEN,
        csrf_token=CSRF_TOKEN,
    )

    sessions.get_active_for_authentication_by_token_sha256.assert_awaited_once()


@pytest.mark.parametrize("csrf_token", [None, "", "short", "x" * 43])
async def test_missing_malformed_or_mismatched_csrf_fails(
    csrf_token: str | None,
) -> None:
    service, _, sessions = _service()
    sessions.get_active_for_authentication_by_token_sha256.return_value = _user_session(_user())

    with pytest.raises(CsrfError):
        await service.validate_csrf(
            session_token=SESSION_TOKEN,
            csrf_token=csrf_token,
        )


def test_capability_matrix_matches_owner_editor_viewer_policy() -> None:
    known_capabilities = frozenset(
        {
            Capability.KNOWLEDGE_BASE_CREATE,
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.DOCUMENT_UPLOAD,
            Capability.INGESTION_JOB_READ,
            Capability.INGESTION_JOB_RETRY,
        }
    )
    owner_and_editor = frozenset(
        {
            Capability.KNOWLEDGE_BASE_CREATE,
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.DOCUMENT_UPLOAD,
            Capability.INGESTION_JOB_READ,
            Capability.INGESTION_JOB_RETRY,
        }
    )
    assert frozenset(Capability) == known_capabilities
    assert capabilities_for(KnowledgeBaseRole.OWNER) == owner_and_editor
    assert capabilities_for(KnowledgeBaseRole.EDITOR) == owner_and_editor
    assert capabilities_for(KnowledgeBaseRole.VIEWER) == frozenset(
        {
            Capability.KNOWLEDGE_BASE_CREATE,
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.INGESTION_JOB_READ,
        }
    )
    assert capabilities_for(None) == frozenset({Capability.KNOWLEDGE_BASE_CREATE})
    assert capabilities_for("future-unmapped-role") == frozenset({Capability.KNOWLEDGE_BASE_CREATE})


def test_unmapped_role_policy_defaults_to_no_object_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(
        authorization._ROLE_CAPABILITIES,
        KnowledgeBaseRole.OWNER,
    )

    assert capabilities_for(KnowledgeBaseRole.OWNER) == frozenset(
        {Capability.KNOWLEDGE_BASE_CREATE}
    )


def test_capability_requirement_is_centralized_and_generic() -> None:
    require_capability(KnowledgeBaseRole.VIEWER, Capability.DOCUMENT_READ)
    require_capability(None, Capability.KNOWLEDGE_BASE_CREATE)

    with pytest.raises(AuthorizationError) as exc_info:
        require_capability(KnowledgeBaseRole.VIEWER, Capability.DOCUMENT_UPLOAD)

    assert exc_info.value.public_message == AuthorizationError.message
