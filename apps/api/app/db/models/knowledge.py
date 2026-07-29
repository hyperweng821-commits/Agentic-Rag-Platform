"""Durable PostgreSQL records for knowledge intake, ingestion, and access."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentStatus(StrEnum):
    """Durable document lifecycle states available in AF-1."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJobStatus(StrEnum):
    """Durable ingestion-job states shared by AF-1 and the AF-2 foundation."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeBaseRole(StrEnum):
    """Roles granted by a knowledge-base membership."""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class TimestampMixin:
    """Server-timestamped fields shared by durable knowledge records."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    """A local user whose password is stored only as an Argon2id hash."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "char_length(btrim(email)) > 0 AND email = lower(email) AND email = btrim(email)",
            name="normalized_email",
        ),
        CheckConstraint(
            "char_length(btrim(password_hash)) > 0 AND password_hash LIKE '$argon2id$%'",
            name="valid_password_hash",
        ),
        Index("ix_users_is_active_id", "is_active", "id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    knowledge_base_memberships: Mapped[list["KnowledgeBaseMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserSession(TimestampMixin, Base):
    """A revocable session containing only digests of opaque browser tokens."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("token_sha256", name="uq_user_sessions_token_sha256"),
        CheckConstraint(
            "token_sha256 ~ '^[0-9a-f]{64}$'",
            name="valid_token_sha256",
        ),
        CheckConstraint(
            "csrf_token_sha256 ~ '^[0-9a-f]{64}$'",
            name="valid_csrf_token_sha256",
        ),
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index(
            "ix_user_sessions_active_user_expires_at",
            "user_id",
            "revoked_at",
            "expires_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    csrf_token_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class KnowledgeBase(TimestampMixin, Base):
    """A named boundary for deduplicated private documents."""

    __tablename__ = "knowledge_bases"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 200",
            name="name_length",
        ),
        CheckConstraint(
            "description IS NULL OR char_length(description) <= 2000",
            name="description_length",
        ),
        Index("ix_knowledge_bases_created_at_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    memberships: Mapped[list["KnowledgeBaseMembership"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class KnowledgeBaseMembership(TimestampMixin, Base):
    """A user's role within one private knowledge-base boundary."""

    __tablename__ = "knowledge_base_memberships"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_base_id",
            "user_id",
            name="uq_knowledge_base_memberships_knowledge_base_id_user_id",
        ),
        CheckConstraint(
            "role IN ('owner', 'editor', 'viewer')",
            name="valid_role",
        ),
        Index(
            "ix_knowledge_base_memberships_user_id_knowledge_base_id",
            "user_id",
            "knowledge_base_id",
        ),
    )

    knowledge_base_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="knowledge_base_memberships")


class Document(TimestampMixin, Base):
    """Stored source-file metadata and its durable ingestion state."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_base_id",
            "sha256",
            name="uq_documents_knowledge_base_id_sha256",
        ),
        UniqueConstraint("storage_key", name="uq_documents_storage_key"),
        CheckConstraint("size_bytes > 0", name="positive_size"),
        CheckConstraint("char_length(sha256) = 64", name="sha256_length"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_status",
        ),
        Index(
            "ix_documents_knowledge_base_created_at_id",
            "knowledge_base_id",
            "created_at",
            "id",
        ),
        Index("ix_documents_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    knowledge_base_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PENDING.value,
        server_default=DocumentStatus.PENDING.value,
    )

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="documents")
    ingestion_job: Mapped["IngestionJob"] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
        passive_deletes=True,
    )


class IngestionJob(TimestampMixin, Base):
    """One durable, idempotently retryable ingestion job per document."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_ingestion_jobs_document_id"),
        CheckConstraint("attempt_count >= 0", name="nonnegative_attempt_count"),
        CheckConstraint("max_attempts > 0", name="positive_max_attempts"),
        CheckConstraint(
            "attempt_count <= max_attempts",
            name="attempt_count_within_max_attempts",
        ),
        CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="progress_percent_range",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_status",
        ),
        CheckConstraint(
            "claimed_by IS NULL OR char_length(btrim(claimed_by)) BETWEEN 1 AND 255",
            name="claimed_by_nonblank",
        ),
        CheckConstraint(
            "("
            "claimed_by IS NULL AND claimed_at IS NULL AND lease_expires_at IS NULL"
            ") OR ("
            "claimed_by IS NOT NULL AND claimed_at IS NOT NULL "
            "AND lease_expires_at IS NOT NULL"
            ")",
            name="lease_fields_consistent",
        ),
        CheckConstraint(
            "lease_expires_at IS NULL OR lease_expires_at > claimed_at",
            name="lease_window",
        ),
        CheckConstraint(
            "safe_error_message IS NULL OR char_length(safe_error_message) <= 1000",
            name="safe_error_message_length",
        ),
        Index("ix_ingestion_jobs_status_created_at", "status", "created_at"),
        Index("ix_ingestion_jobs_status_next_retry_at", "status", "next_retry_at"),
        Index(
            "ix_ingestion_jobs_status_lease_expires_at",
            "status",
            "lease_expires_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=IngestionJobStatus.PENDING.value,
        server_default=IngestionJobStatus.PENDING.value,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    claimed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    safe_error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="ingestion_job")


class DocumentChunk(TimestampMixin, Base):
    """PostgreSQL-authoritative normalized text for one ordered document chunk."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_id_chunk_index",
        ),
        CheckConstraint("chunk_index >= 0", name="nonnegative_chunk_index"),
        CheckConstraint("token_count >= 0", name="nonnegative_token_count"),
        CheckConstraint(
            "char_length(btrim(normalized_text)) > 0",
            name="nonempty_normalized_text",
        ),
        CheckConstraint(
            "content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$'",
            name="valid_content_sha256",
        ),
        CheckConstraint(
            "("
            "start_offset IS NULL AND end_offset IS NULL"
            ") OR ("
            "start_offset IS NOT NULL AND end_offset IS NOT NULL "
            "AND start_offset >= 0 AND end_offset > start_offset"
            ")",
            name="valid_source_offsets",
        ),
        CheckConstraint(
            "("
            "page_start IS NULL AND page_end IS NULL"
            ") OR ("
            "page_start IS NOT NULL AND page_end IS NOT NULL "
            "AND page_start > 0 AND page_end >= page_start"
            ")",
            name="valid_page_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")
