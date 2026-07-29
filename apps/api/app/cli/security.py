"""Operator commands for local users and fail-closed legacy knowledge bases."""

import argparse
import asyncio
import getpass
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories import KnowledgeBaseMembershipRepository, UserRepository
from app.db.session import async_session_maker, dispose_engine
from app.security import (
    Argon2idPasswordHasher,
    PasswordHasher,
    normalize_email,
    validate_password_length,
)


class OperatorCommandError(Exception):
    """A safe operator-facing command failure."""


class SecurityOperatorService:
    """Deterministic service boundary consumed by the operator CLI."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._session = session
        self._password_hasher = password_hasher or Argon2idPasswordHasher()
        self._users = UserRepository(session)
        self._memberships = KnowledgeBaseMembershipRepository(session)

    async def bootstrap_user(self, *, email: str, password: str) -> User:
        """Create exactly one active local user with an Argon2id password hash."""
        try:
            normalized_email = normalize_email(email)
            validate_password_length(password)
            password_hash = await asyncio.to_thread(
                self._password_hasher.hash_password,
                password,
            )
        except ValueError as exc:
            raise OperatorCommandError(str(exc)) from exc

        try:
            async with self._session.begin():
                if await self._users.get_for_operator_by_email(normalized_email) is not None:
                    raise OperatorCommandError("A user with that email already exists.")
                user = User(
                    email=normalized_email,
                    password_hash=password_hash,
                    is_active=True,
                )
                await self._users.add_for_operator(user)
        except IntegrityError as exc:
            raise OperatorCommandError("A user with that email already exists.") from exc
        return user

    async def claim_legacy_knowledge_bases(
        self,
        *,
        owner_email: str,
        dry_run: bool,
    ) -> int:
        """Claim only knowledge bases that currently have no memberships."""
        try:
            normalized_email = normalize_email(owner_email)
        except ValueError as exc:
            raise OperatorCommandError(str(exc)) from exc

        async with self._session.begin():
            owner = await self._users.get_for_operator_by_email(
                normalized_email,
                for_update=not dry_run,
            )
            if owner is None:
                raise OperatorCommandError("The requested owner user does not exist.")
            if not owner.is_active:
                raise OperatorCommandError("The requested owner user is inactive.")
            if dry_run:
                return await self._memberships.count_unowned_internal()
            return await self._memberships.claim_unowned_internal(
                owner_user_id=owner.id,
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage AgentForge local access-boundary bootstrap data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    bootstrap = commands.add_parser(
        "bootstrap-user",
        help="Create one active local user.",
    )
    bootstrap.add_argument("--email", required=True)

    claim = commands.add_parser(
        "claim-legacy-knowledge-bases",
        help="Assign one existing user as owner of every currently unowned knowledge base.",
    )
    claim.add_argument("--owner-email", required=True)
    claim.add_argument("--dry-run", action="store_true")
    return parser


async def _run(args: argparse.Namespace, *, password: str | None = None) -> int:
    async with async_session_maker() as session:
        service = SecurityOperatorService(session)
        if args.command == "bootstrap-user":
            if password is None:
                raise OperatorCommandError("A password is required.")
            await service.bootstrap_user(email=args.email, password=password)
            return 1
        if args.command == "claim-legacy-knowledge-bases":
            return await service.claim_legacy_knowledge_bases(
                owner_email=args.owner_email,
                dry_run=args.dry_run,
            )
    raise OperatorCommandError("Unknown operator command.")


async def _run_and_dispose(args: argparse.Namespace, *, password: str | None) -> int:
    try:
        return await _run(args, password=password)
    finally:
        await dispose_engine()


def main(argv: Sequence[str] | None = None) -> int:
    """Parse operator input, execute one transaction, and print counts only."""
    args = _build_parser().parse_args(argv)
    password: str | None = None
    if args.command == "bootstrap-user":
        password = getpass.getpass("Password: ")
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            print("Error: passwords do not match.")
            return 2

    try:
        count = asyncio.run(_run_and_dispose(args, password=password))
    except OperatorCommandError as exc:
        print(f"Error: {exc}")
        return 2

    action = "would change" if getattr(args, "dry_run", False) else "changed"
    print(f"Records {action}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
