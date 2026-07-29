"""Add the AF-2S local-user and knowledge-access boundary.

Revision ID: 20260729_0004
Revises: 20260728_0003
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260729_0004"
down_revision: str | None = "20260728_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add local users, opaque sessions, and explicit KB memberships."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(btrim(email)) > 0 AND email = lower(email) AND email = btrim(email)",
            name=op.f("ck_users_normalized_email"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(password_hash)) > 0 AND password_hash LIKE '$argon2id$%'",
            name=op.f("ck_users_valid_password_hash"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(
        "ix_users_is_active_id",
        "users",
        ["is_active", "id"],
        unique=False,
    )

    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("token_sha256", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_sha256", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "token_sha256 ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_user_sessions_valid_token_sha256"),
        ),
        sa.CheckConstraint(
            "csrf_token_sha256 ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_user_sessions_valid_csrf_token_sha256"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sessions")),
        sa.UniqueConstraint(
            "token_sha256",
            name=op.f("uq_user_sessions_token_sha256"),
        ),
    )
    op.create_index(
        "ix_user_sessions_user_id",
        "user_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_sessions_expires_at",
        "user_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_sessions_active_user_expires_at",
        "user_sessions",
        ["user_id", "revoked_at", "expires_at"],
        unique=False,
    )

    op.create_table(
        "knowledge_base_memberships",
        sa.Column(
            "knowledge_base_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'editor', 'viewer')",
            name=op.f("ck_knowledge_base_memberships_valid_role"),
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            name=op.f("fk_knowledge_base_memberships_knowledge_base_id_knowledge_bases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_knowledge_base_memberships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "knowledge_base_id",
            "user_id",
            name=op.f("pk_knowledge_base_memberships"),
        ),
        sa.UniqueConstraint(
            "knowledge_base_id",
            "user_id",
            name=op.f("uq_knowledge_base_memberships_knowledge_base_id_user_id"),
        ),
    )
    op.create_index(
        "ix_knowledge_base_memberships_user_id_knowledge_base_id",
        "knowledge_base_memberships",
        ["user_id", "knowledge_base_id"],
        unique=False,
    )


def downgrade() -> None:
    """Preserve legacy knowledge data but destructively remove AF-2S identity data."""
    op.drop_index(
        "ix_knowledge_base_memberships_user_id_knowledge_base_id",
        table_name="knowledge_base_memberships",
    )
    op.drop_table("knowledge_base_memberships")

    op.drop_index(
        "ix_user_sessions_active_user_expires_at",
        table_name="user_sessions",
    )
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_users_is_active_id", table_name="users")
    op.drop_table("users")
