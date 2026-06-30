"""add_history_entries_table

Revision ID: 9a8fa02fac9a
Revises: 0004
Create Date: 2026-06-30 18:01:22.295933+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a8fa02fac9a'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('history_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('cv_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_history_entries_cv_id'), 'history_entries', ['cv_id'], unique=False)
    op.create_index(op.f('ix_history_entries_user_id'), 'history_entries', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_history_entries_user_id'), table_name='history_entries')
    op.drop_index(op.f('ix_history_entries_cv_id'), table_name='history_entries')
    op.drop_table('history_entries')
