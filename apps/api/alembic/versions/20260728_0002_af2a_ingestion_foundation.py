"""Add the AF-2A ingestion persistence foundation.

Revision ID: 20260728_0002
Revises: 20260727_0001
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260728_0002"
down_revision: str | None = "20260727_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add durable job leases, retry metadata, progress, and document chunks."""
    op.add_column(
        "ingestion_jobs",
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("claimed_by", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        "UPDATE ingestion_jobs "
        "SET max_attempts = GREATEST(attempt_count, 3) "
        "WHERE attempt_count > max_attempts"
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_positive_max_attempts"),
        "ingestion_jobs",
        "max_attempts > 0",
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_attempt_count_within_max_attempts"),
        "ingestion_jobs",
        "attempt_count <= max_attempts",
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_progress_percent_range"),
        "ingestion_jobs",
        "progress_percent BETWEEN 0 AND 100",
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_claimed_by_nonblank"),
        "ingestion_jobs",
        "claimed_by IS NULL OR char_length(btrim(claimed_by)) BETWEEN 1 AND 255",
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_lease_fields_consistent"),
        "ingestion_jobs",
        "("
        "claimed_by IS NULL AND claimed_at IS NULL AND lease_expires_at IS NULL"
        ") OR ("
        "claimed_by IS NOT NULL AND claimed_at IS NOT NULL "
        "AND lease_expires_at IS NOT NULL"
        ")",
    )
    op.create_check_constraint(
        op.f("ck_ingestion_jobs_lease_window"),
        "ingestion_jobs",
        "lease_expires_at IS NULL OR lease_expires_at > claimed_at",
    )
    op.create_index(
        "ix_ingestion_jobs_status_next_retry_at",
        "ingestion_jobs",
        ["status", "next_retry_at"],
        unique=False,
    )
    op.create_index(
        "ix_ingestion_jobs_status_lease_expires_at",
        "ingestion_jobs",
        ["status", "lease_expires_at"],
        unique=False,
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name=op.f("ck_document_chunks_nonnegative_chunk_index"),
        ),
        sa.CheckConstraint(
            "token_count >= 0",
            name=op.f("ck_document_chunks_nonnegative_token_count"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(normalized_text)) > 0",
            name=op.f("ck_document_chunks_nonempty_normalized_text"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_chunks_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_id_chunk_index",
        ),
    )


def downgrade() -> None:
    """Remove only the AF-2A schema additions."""
    op.drop_table("document_chunks")
    op.drop_index(
        "ix_ingestion_jobs_status_lease_expires_at",
        table_name="ingestion_jobs",
    )
    op.drop_index(
        "ix_ingestion_jobs_status_next_retry_at",
        table_name="ingestion_jobs",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_lease_window"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_lease_fields_consistent"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_claimed_by_nonblank"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_progress_percent_range"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_attempt_count_within_max_attempts"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_ingestion_jobs_positive_max_attempts"),
        "ingestion_jobs",
        type_="check",
    )
    op.drop_column("ingestion_jobs", "next_retry_at")
    op.drop_column("ingestion_jobs", "lease_expires_at")
    op.drop_column("ingestion_jobs", "claimed_at")
    op.drop_column("ingestion_jobs", "claimed_by")
    op.drop_column("ingestion_jobs", "progress_percent")
    op.drop_column("ingestion_jobs", "max_attempts")
