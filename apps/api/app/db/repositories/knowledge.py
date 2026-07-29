"""Explicit SQLAlchemy queries for knowledge, ingestion, and access scope."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, delete, exists, func, literal, or_, select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)

type KnowledgeBaseAccess = tuple[KnowledgeBase, KnowledgeBaseRole]
type DocumentAccess = tuple[Document, KnowledgeBaseRole]
type IngestionJobAccess = tuple[IngestionJob, KnowledgeBaseRole]

_LEGACY_CLAIM_LOCK_NAMESPACE = 1_095_115_347
_LEGACY_CLAIM_LOCK_KEY = 1


@dataclass(frozen=True, slots=True)
class AuthenticationUserSnapshot:
    """Primitive user state retained after the authentication read transaction."""

    user_id: UUID
    email: str
    is_active: bool
    password_hash: str


class UserRepository:
    """Persistence operations for local users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_for_operator(self, user: User) -> None:
        self._session.add(user)
        await self._session.flush()

    async def get_for_authentication_by_email(
        self,
        email: str,
    ) -> AuthenticationUserSnapshot | None:
        statement = select(
            User.id,
            User.email,
            User.is_active,
            User.password_hash,
        ).where(User.email == email)
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        return AuthenticationUserSnapshot(
            user_id=row.id,
            email=row.email,
            is_active=row.is_active,
            password_hash=row.password_hash,
        )

    async def get_locked_for_authentication(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id).with_for_update()
        user: User | None = await self._session.scalar(statement)
        return user

    async def update_password_hash_for_authentication(
        self,
        user: User,
        *,
        password_hash: str,
    ) -> None:
        user.password_hash = password_hash
        await self._session.flush()

    async def get_for_operator_by_email(
        self,
        email: str,
        *,
        for_update: bool = False,
    ) -> User | None:
        statement = select(User).where(User.email == email)
        if for_update:
            statement = statement.with_for_update()
        user: User | None = await self._session.scalar(statement)
        return user


class UserSessionRepository:
    """Persistence operations for server-side opaque sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_for_authentication(self, user_session: UserSession) -> None:
        self._session.add(user_session)
        await self._session.flush()

    async def get_active_for_authentication_by_token_sha256(
        self,
        token_sha256: str,
        *,
        now: datetime,
    ) -> UserSession | None:
        statement = (
            select(UserSession)
            .where(
                UserSession.token_sha256 == token_sha256,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .options(selectinload(UserSession.user))
        )
        user_session: UserSession | None = await self._session.scalar(statement)
        return user_session

    async def revoke_for_authentication(
        self,
        user_session: UserSession,
        *,
        revoked_at: datetime,
    ) -> None:
        user_session.revoked_at = revoked_at
        await self._session.flush()

    async def touch_for_authentication(
        self,
        user_session: UserSession,
        *,
        seen_at: datetime,
    ) -> None:
        user_session.last_seen_at = seen_at
        await self._session.flush()


class KnowledgeBaseRepository:
    """Persistence operations for knowledge bases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_with_owner(
        self,
        knowledge_base: KnowledgeBase,
        *,
        owner_user_id: UUID,
    ) -> None:
        """Add a knowledge base and its owner membership in one transaction."""
        knowledge_base.memberships.append(
            KnowledgeBaseMembership(
                user_id=owner_user_id,
                role=KnowledgeBaseRole.OWNER.value,
            )
        )
        self._session.add(knowledge_base)
        await self._session.flush()

    async def get_internal(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        """Get a knowledge base without user scope for worker/rebuild workflows."""
        return await self._session.get(KnowledgeBase, knowledge_base_id)

    async def get_for_user(
        self,
        knowledge_base_id: UUID,
        *,
        user_id: UUID,
    ) -> KnowledgeBaseAccess | None:
        statement = (
            select(KnowledgeBase, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        knowledge_base, role = row
        return knowledge_base, KnowledgeBaseRole(role)

    async def get_upload_target_for_user(
        self,
        knowledge_base_id: UUID,
        *,
        user_id: UUID,
    ) -> KnowledgeBaseAccess | None:
        """Resolve and lock an upload target through its caller's membership."""
        statement = (
            select(KnowledgeBase, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .with_for_update()
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        knowledge_base, role = row
        return knowledge_base, KnowledgeBaseRole(role)

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        limit: int,
        offset: int,
    ) -> list[KnowledgeBaseAccess]:
        statement = (
            select(KnowledgeBase, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(KnowledgeBaseMembership.user_id == user_id)
            .order_by(KnowledgeBase.created_at.asc(), KnowledgeBase.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).all()
        return [(knowledge_base, KnowledgeBaseRole(role)) for knowledge_base, role in rows]


class KnowledgeBaseMembershipRepository:
    """Persistence operations for knowledge-base memberships."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_unowned_internal(self) -> int:
        has_any_membership = exists(
            select(KnowledgeBaseMembership.knowledge_base_id).where(
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id
            )
        )
        statement = select(func.count()).select_from(KnowledgeBase).where(~has_any_membership)
        count = await self._session.scalar(statement)
        return int(count or 0)

    async def claim_unowned_internal(self, *, owner_user_id: UUID) -> int:
        """Idempotently add owner membership only to currently unowned KBs."""
        # Serialize operator claims so two different owners cannot both observe
        # and claim the same membership-free knowledge base.
        await self._session.execute(
            select(
                func.pg_advisory_xact_lock(
                    _LEGACY_CLAIM_LOCK_NAMESPACE,
                    _LEGACY_CLAIM_LOCK_KEY,
                )
            )
        )
        has_any_membership = exists(
            select(KnowledgeBaseMembership.knowledge_base_id).where(
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id
            )
        )
        eligible = select(
            KnowledgeBase.id,
            literal(owner_user_id, type_=PostgreSQLUUID(as_uuid=True)),
            literal(KnowledgeBaseRole.OWNER.value),
        ).where(~has_any_membership)
        statement = (
            insert(KnowledgeBaseMembership)
            .from_select(
                ["knowledge_base_id", "user_id", "role"],
                eligible,
            )
            .on_conflict_do_nothing(
                index_elements=["knowledge_base_id", "user_id"],
            )
            .returning(KnowledgeBaseMembership.knowledge_base_id)
        )
        claimed_ids = (await self._session.scalars(statement)).all()
        await self._session.flush()
        return len(claimed_ids)


class DocumentRepository:
    """Persistence operations for document metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_authorized_upload(self, document: Document) -> None:
        """Add metadata after a scoped upload target has been locked."""
        self._session.add(document)
        await self._session.flush()

    async def get_internal(self, document_id: UUID) -> Document | None:
        """Get a document without user scope for worker/rebuild workflows."""
        statement = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.ingestion_job))
        )
        document: Document | None = await self._session.scalar(statement)
        return document

    async def get_by_digest_for_user(
        self,
        *,
        knowledge_base_id: UUID,
        sha256: str,
        user_id: UUID,
    ) -> DocumentAccess | None:
        """Find a duplicate only through the uploader's current membership."""
        statement = (
            select(Document, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == Document.knowledge_base_id,
            )
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.sha256 == sha256,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .options(selectinload(Document.ingestion_job))
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        document, role = row
        return document, KnowledgeBaseRole(role)

    async def list_for_knowledge_base_internal(
        self,
        knowledge_base_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Document]:
        """List documents without user scope for worker/rebuild workflows."""
        statement: Select[tuple[Document]] = (
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(Document.created_at.asc(), Document.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.scalars(statement)).all())

    async def get_for_user(
        self,
        document_id: UUID,
        *,
        user_id: UUID,
    ) -> DocumentAccess | None:
        statement = (
            select(Document, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == Document.knowledge_base_id,
            )
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                Document.id == document_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .options(selectinload(Document.ingestion_job))
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        document, role = row
        return document, KnowledgeBaseRole(role)

    async def list_for_knowledge_base_for_user(
        self,
        knowledge_base_id: UUID,
        *,
        user_id: UUID,
        limit: int,
        offset: int,
    ) -> list[DocumentAccess]:
        statement = (
            select(Document, KnowledgeBaseMembership.role)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == Document.knowledge_base_id,
            )
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .order_by(Document.created_at.asc(), Document.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).all()
        return [(document, KnowledgeBaseRole(role)) for document, role in rows]


class DocumentChunkRepository:
    """Persistence operations for ordered, PostgreSQL-authoritative chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_document_internal(
        self,
        document_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        if limit is not None:
            if limit < 1:
                raise ValueError("limit must be positive")
            statement = statement.limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def replace_for_document_internal(
        self,
        document_id: UUID,
        chunks: Sequence[DocumentChunk],
    ) -> None:
        if any(chunk.document_id != document_id for chunk in chunks):
            raise ValueError("Every replacement chunk must match the target document_id.")

        await self._session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        self._session.add_all(list(chunks))
        await self._session.flush()


class IngestionJobRepository:
    """Persistence operations for one durable job per document."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_for_authorized_upload(self, job: IngestionJob) -> None:
        """Add a job belonging to a scoped and locked upload target."""
        self._session.add(job)
        await self._session.flush()

    async def get_for_user(
        self,
        job_id: UUID,
        *,
        user_id: UUID,
    ) -> IngestionJobAccess | None:
        statement = (
            select(IngestionJob, KnowledgeBaseMembership.role)
            .join(Document, Document.id == IngestionJob.document_id)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == Document.knowledge_base_id,
            )
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                IngestionJob.id == job_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .options(selectinload(IngestionJob.document))
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        job, role = row
        return job, KnowledgeBaseRole(role)

    async def get_retry_target_for_user(
        self,
        job_id: UUID,
        *,
        user_id: UUID,
        for_update: bool = True,
    ) -> IngestionJobAccess | None:
        statement = (
            select(IngestionJob, KnowledgeBaseMembership.role)
            .join(Document, Document.id == IngestionJob.document_id)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == Document.knowledge_base_id,
            )
            .join(
                KnowledgeBaseMembership,
                KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                IngestionJob.id == job_id,
                KnowledgeBaseMembership.user_id == user_id,
            )
            .options(selectinload(IngestionJob.document))
        )
        if for_update:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        job, role = row
        return job, KnowledgeBaseRole(role)

    async def claim_next_internal(
        self,
        *,
        worker_id: str,
        claimed_at: datetime,
        lease_expires_at: datetime,
    ) -> IngestionJob | None:
        """Claim one due pending job while concurrent workers skip its row lock."""
        if not worker_id.strip():
            raise ValueError("worker_id must not be blank")
        if lease_expires_at <= claimed_at:
            raise ValueError("lease_expires_at must be later than claimed_at")

        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.status == IngestionJobStatus.PENDING.value,
                IngestionJob.attempt_count < IngestionJob.max_attempts,
                or_(
                    IngestionJob.next_retry_at.is_(None),
                    IngestionJob.next_retry_at <= claimed_at,
                ),
            )
            .options(selectinload(IngestionJob.document))
            .order_by(
                func.coalesce(IngestionJob.next_retry_at, IngestionJob.created_at).asc(),
                IngestionJob.created_at.asc(),
                IngestionJob.id.asc(),
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job: IngestionJob | None = await self._session.scalar(statement)
        if job is None:
            return None

        job.status = IngestionJobStatus.PROCESSING.value
        job.attempt_count += 1
        job.progress_percent = 0
        job.claimed_by = worker_id
        job.claimed_at = claimed_at
        job.lease_expires_at = lease_expires_at
        job.next_retry_at = None
        job.error_code = None
        job.safe_error_message = None
        job.started_at = claimed_at
        job.finished_at = None
        job.document.status = DocumentStatus.PROCESSING.value
        await self._session.flush()
        return job

    async def lock_expired_leases_internal(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[IngestionJob]:
        """Lock a bounded set of expired jobs without waiting on other recoverers."""
        if limit < 1:
            raise ValueError("limit must be positive")
        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.status == IngestionJobStatus.PROCESSING.value,
                IngestionJob.lease_expires_at.is_not(None),
                IngestionJob.lease_expires_at <= now,
            )
            .options(selectinload(IngestionJob.document))
            .order_by(IngestionJob.lease_expires_at.asc(), IngestionJob.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list((await self._session.scalars(statement)).all())

    async def get_owned_processing_internal(
        self,
        job_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        for_update: bool = False,
    ) -> IngestionJob | None:
        """Read an unexpired processing job only when the caller still owns its lease."""
        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.id == job_id,
                IngestionJob.status == IngestionJobStatus.PROCESSING.value,
                IngestionJob.claimed_by == worker_id,
                IngestionJob.lease_expires_at > now,
            )
            .options(selectinload(IngestionJob.document))
        )
        if for_update:
            statement = statement.with_for_update()
        job: IngestionJob | None = await self._session.scalar(statement)
        return job
