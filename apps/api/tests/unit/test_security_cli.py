"""AF-2S1 deterministic operator CLI and service tests."""

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import cast
from unittest.mock import AsyncMock, Mock, call
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import security as security_cli
from app.cli.security import OperatorCommandError, SecurityOperatorService
from app.db.models import User
from app.security import MAX_PASSWORD_LENGTH


class TransactionContext(AbstractAsyncContextManager[None]):
    """Minimal transaction context used by the repository-free service tests."""

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class FakeSession:
    """Expose only the transaction boundary consumed by the operator service."""

    def begin(self) -> TransactionContext:
        return TransactionContext()


class StubPasswordHasher:
    """Record plaintext input and return one deterministic non-plaintext hash."""

    def __init__(self) -> None:
        self.passwords: list[str] = []
        self.password_hash = "".join(("$argon2id$", "deterministic-test-hash"))

    def hash_password(self, password: str) -> str:
        self.passwords.append(password)
        return self.password_hash

    def verify_password(self, password: str, password_hash: str | None) -> bool:
        raise AssertionError("The bootstrap command must not verify passwords.")

    def needs_rehash(self, password_hash: str) -> bool:
        raise AssertionError("The bootstrap command must not inspect rehash state.")


def _service() -> tuple[SecurityOperatorService, StubPasswordHasher, AsyncMock, AsyncMock]:
    password_hasher = StubPasswordHasher()
    service = SecurityOperatorService(
        cast(AsyncSession, FakeSession()),
        password_hasher=password_hasher,
    )
    users = AsyncMock()
    memberships = AsyncMock()
    service._users = users
    service._memberships = memberships
    return service, password_hasher, users, memberships


def _user(*, email: str = "owner@example.com", active: bool = True) -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash="".join(("$argon2id$", "existing-hash")),
        is_active=active,
    )


async def test_bootstrap_user_normalizes_email_and_persists_only_the_hash(
    capsys: pytest.CaptureFixture[str],
) -> None:
    service, password_hasher, users, _ = _service()
    users.get_for_operator_by_email.return_value = None
    assigned_user_id = uuid4()

    async def add(user: User) -> None:
        user.id = assigned_user_id

    users.add_for_operator.side_effect = add
    password = "".join(("operator-", "passphrase"))

    user = await service.bootstrap_user(
        email=" OWNER@Example.COM ",
        password=password,
    )

    users.get_for_operator_by_email.assert_awaited_once_with("owner@example.com")
    users.add_for_operator.assert_awaited_once_with(user)
    assert user.id == assigned_user_id
    assert user.email == "owner@example.com"
    assert user.password_hash == password_hasher.password_hash
    assert user.password_hash != password
    assert password_hasher.passwords == [password]
    output = capsys.readouterr().out
    assert password not in output
    assert password_hasher.password_hash not in output


async def test_bootstrap_user_rejects_duplicate_normalized_email() -> None:
    service, password_hasher, users, _ = _service()
    users.get_for_operator_by_email.return_value = _user()
    password = "".join(("duplicate-", "passphrase"))

    with pytest.raises(
        OperatorCommandError,
        match=r"A user with that email already exists\.",
    ):
        await service.bootstrap_user(
            email=" Owner@Example.COM ",
            password=password,
        )

    assert password_hasher.passwords == [password]
    users.get_for_operator_by_email.assert_awaited_once_with("owner@example.com")
    users.add_for_operator.assert_not_awaited()


async def test_claim_legacy_knowledge_bases_dry_run_is_read_only() -> None:
    service, _, users, memberships = _service()
    owner = _user()
    users.get_for_operator_by_email.return_value = owner
    memberships.count_unowned_internal.return_value = 4

    count = await service.claim_legacy_knowledge_bases(
        owner_email=" OWNER@EXAMPLE.COM ",
        dry_run=True,
    )

    assert count == 4
    users.get_for_operator_by_email.assert_awaited_once_with(
        "owner@example.com",
        for_update=False,
    )
    memberships.count_unowned_internal.assert_awaited_once_with()
    memberships.claim_unowned_internal.assert_not_awaited()


async def test_claim_legacy_knowledge_bases_is_idempotent_via_scoped_repository() -> None:
    service, _, users, memberships = _service()
    owner = _user()
    users.get_for_operator_by_email.return_value = owner
    memberships.claim_unowned_internal.side_effect = [3, 0]

    first_count = await service.claim_legacy_knowledge_bases(
        owner_email="owner@example.com",
        dry_run=False,
    )
    second_count = await service.claim_legacy_knowledge_bases(
        owner_email="owner@example.com",
        dry_run=False,
    )

    assert first_count == 3
    assert second_count == 0
    assert memberships.claim_unowned_internal.await_args_list == [
        call(owner_user_id=owner.id),
        call(owner_user_id=owner.id),
    ]
    assert users.get_for_operator_by_email.await_args_list == [
        call("owner@example.com", for_update=True),
        call("owner@example.com", for_update=True),
    ]
    memberships.count_unowned_internal.assert_not_awaited()


async def test_claim_legacy_knowledge_bases_requires_an_existing_owner() -> None:
    service, _, users, memberships = _service()
    users.get_for_operator_by_email.return_value = None

    with pytest.raises(
        OperatorCommandError,
        match=r"The requested owner user does not exist\.",
    ):
        await service.claim_legacy_knowledge_bases(
            owner_email="missing@example.com",
            dry_run=False,
        )

    memberships.claim_unowned_internal.assert_not_awaited()


@pytest.mark.parametrize("dry_run", [False, True], ids=["write", "dry-run"])
async def test_claim_legacy_knowledge_bases_rejects_inactive_owner(
    dry_run: bool,
) -> None:
    service, _, users, memberships = _service()
    users.get_for_operator_by_email.return_value = _user(active=False)

    with pytest.raises(
        OperatorCommandError,
        match=r"The requested owner user is inactive\.",
    ):
        await service.claim_legacy_knowledge_bases(
            owner_email="owner@example.com",
            dry_run=dry_run,
        )

    users.get_for_operator_by_email.assert_awaited_once_with(
        "owner@example.com",
        for_update=not dry_run,
    )
    memberships.count_unowned_internal.assert_not_awaited()
    memberships.claim_unowned_internal.assert_not_awaited()


async def test_claim_dry_run_rejects_missing_owner_without_counting() -> None:
    service, _, users, memberships = _service()
    users.get_for_operator_by_email.return_value = None

    with pytest.raises(OperatorCommandError, match="does not exist"):
        await service.claim_legacy_knowledge_bases(
            owner_email="missing@example.com",
            dry_run=True,
        )

    memberships.count_unowned_internal.assert_not_awaited()
    memberships.claim_unowned_internal.assert_not_awaited()


async def test_bootstrap_password_limit_is_consistent_and_precedes_hashing() -> None:
    maximum = "m" * MAX_PASSWORD_LENGTH
    service, password_hasher, users, _ = _service()
    users.get_for_operator_by_email.return_value = None

    created = await service.bootstrap_user(
        email="maximum@example.com",
        password=maximum,
    )

    assert created.email == "maximum@example.com"
    assert password_hasher.passwords == [maximum]
    users.add_for_operator.assert_awaited_once_with(created)

    over_limit = "x" * (MAX_PASSWORD_LENGTH + 1)
    second_service, second_hasher, second_users, _ = _service()
    with pytest.raises(OperatorCommandError, match=str(MAX_PASSWORD_LENGTH)) as exc_info:
        await second_service.bootstrap_user(
            email="over-limit@example.com",
            password=over_limit,
        )

    assert over_limit not in str(exc_info.value)
    assert second_hasher.passwords == []
    second_users.get_for_operator_by_email.assert_not_awaited()
    second_users.add_for_operator.assert_not_awaited()


def test_bootstrap_command_reads_and_confirms_password_with_getpass(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    password = "".join(("secure-", "operator-passphrase"))
    password_reader = Mock(side_effect=[password, password])
    runner = AsyncMock(return_value=1)
    monkeypatch.setattr(security_cli.getpass, "getpass", password_reader)
    monkeypatch.setattr(security_cli, "_run_and_dispose", runner)

    result = security_cli.main(
        ["bootstrap-user", "--email", "owner@example.com"],
    )

    assert result == 0
    assert password_reader.call_args_list == [
        call("Password: "),
        call("Confirm password: "),
    ]
    args = runner.await_args.args[0]
    assert args.command == "bootstrap-user"
    assert args.email == "owner@example.com"
    assert runner.await_args.kwargs == {"password": password}
    output = capsys.readouterr().out
    assert output == "Records changed: 1\n"
    assert password not in output
    assert "argon2" not in output.lower()


def test_bootstrap_command_does_not_run_when_password_confirmation_differs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_password = "".join(("first-", "operator-passphrase"))
    second_password = "".join(("second-", "operator-passphrase"))
    runner = AsyncMock()
    monkeypatch.setattr(
        security_cli.getpass,
        "getpass",
        Mock(side_effect=[first_password, second_password]),
    )
    monkeypatch.setattr(security_cli, "_run_and_dispose", runner)

    result = security_cli.main(
        ["bootstrap-user", "--email", "owner@example.com"],
    )

    assert result == 2
    runner.assert_not_awaited()
    output = capsys.readouterr().out
    assert output == "Error: passwords do not match.\n"
    assert first_password not in output
    assert second_password not in output


def test_claim_dry_run_command_never_prompts_for_a_password(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    password_reader = Mock()
    runner = AsyncMock(return_value=5)
    monkeypatch.setattr(security_cli.getpass, "getpass", password_reader)
    monkeypatch.setattr(security_cli, "_run_and_dispose", runner)

    result = security_cli.main(
        [
            "claim-legacy-knowledge-bases",
            "--owner-email",
            "owner@example.com",
            "--dry-run",
        ],
    )

    assert result == 0
    password_reader.assert_not_called()
    args = runner.await_args.args[0]
    assert args.command == "claim-legacy-knowledge-bases"
    assert args.owner_email == "owner@example.com"
    assert args.dry_run is True
    assert runner.await_args.kwargs == {"password": None}
    assert capsys.readouterr().out == "Records would change: 5\n"
