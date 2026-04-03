"""add cv chat_history_json

Revision ID: f8a1c2d3e4b5
Revises: 336ec217b748
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa


revision = "f8a1c2d3e4b5"
down_revision = "336ec217b748"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cvs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("chat_history_json", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("cvs", schema=None) as batch_op:
        batch_op.drop_column("chat_history_json")
