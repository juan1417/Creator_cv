"""initial schema (users, cvs, chat_histories)

Revision ID: 0001
Revises:
Create Date: 2026-06-24

Crea las tres tablas del modelo de dominio con tipos Postgres nativos:
- PKs y FKs como ``UUID``.
- ``context_json`` y ``messages`` como ``JSONB``.
- ``DateTime(timezone=True)`` para timestamps con zona.
- FK ``chat_histories.cv_id`` con ``ON DELETE CASCADE`` (al borrar CV se borra su chat).
- Índices secundarios en ``users.email`` (único), ``cvs.user_id``, ``chat_histories.cv_id``.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "cvs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("context_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_cvs_user_id"),
    )
    op.create_index("ix_cvs_user_id", "cvs", ["user_id"])

    op.create_table(
        "chat_histories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cv_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "messages",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["cv_id"], ["cvs.id"], ondelete="CASCADE", name="fk_chat_cv_id"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_chat_user_id"
        ),
    )
    op.create_index("ix_chat_histories_cv_id", "chat_histories", ["cv_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_histories_cv_id", table_name="chat_histories")
    op.drop_table("chat_histories")
    op.drop_index("ix_cvs_user_id", table_name="cvs")
    op.drop_table("cvs")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
