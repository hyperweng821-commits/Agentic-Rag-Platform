"""Add AF-2B chunk provenance metadata.

Revision ID: 20260728_0003
Revises: 20260728_0002
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0003"
down_revision: str | None = "20260728_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable provenance fields without fabricating metadata for legacy chunks."""
    op.add_column(
        "document_chunks",
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("start_offset", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("end_offset", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("page_start", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("page_end", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_document_chunks_valid_content_sha256"),
        "document_chunks",
        "content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$'",
    )
    op.create_check_constraint(
        op.f("ck_document_chunks_valid_source_offsets"),
        "document_chunks",
        "("
        "start_offset IS NULL AND end_offset IS NULL"
        ") OR ("
        "start_offset IS NOT NULL AND end_offset IS NOT NULL "
        "AND start_offset >= 0 AND end_offset > start_offset"
        ")",
    )
    op.create_check_constraint(
        op.f("ck_document_chunks_valid_page_range"),
        "document_chunks",
        "("
        "page_start IS NULL AND page_end IS NULL"
        ") OR ("
        "page_start IS NOT NULL AND page_end IS NOT NULL "
        "AND page_start > 0 AND page_end >= page_start"
        ")",
    )


def downgrade() -> None:
    """Remove only the AF-2B chunk provenance fields."""
    op.drop_constraint(
        op.f("ck_document_chunks_valid_page_range"),
        "document_chunks",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_document_chunks_valid_source_offsets"),
        "document_chunks",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_document_chunks_valid_content_sha256"),
        "document_chunks",
        type_="check",
    )
    op.drop_column("document_chunks", "page_end")
    op.drop_column("document_chunks", "page_start")
    op.drop_column("document_chunks", "end_offset")
    op.drop_column("document_chunks", "start_offset")
    op.drop_column("document_chunks", "content_sha256")
