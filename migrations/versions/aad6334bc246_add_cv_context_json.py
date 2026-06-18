"""baseline schema and cv context_json

Revision ID: aad6334bc246
Revises:
Create Date: 2026-04-02 12:48:14.266895

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aad6334bc246'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline schema: create users, cvs, cv_sections before adding
    # context_json (which used to assume the tables already existed).
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)

    op.create_table(
        'cvs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('context_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cvs_user_id', 'cvs', ['user_id'], unique=False)

    op.create_table(
        'cv_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cv_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cv_sections_cv_id', 'cv_sections', ['cv_id'], unique=False)


def downgrade():
    op.drop_index('ix_cv_sections_cv_id', table_name='cv_sections')
    op.drop_table('cv_sections')
    op.drop_index('ix_cvs_user_id', table_name='cvs')
    op.drop_table('cvs')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
