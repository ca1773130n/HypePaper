"""add_user_support_to_topics_and_papers

Revision ID: c87e71e8eb12
Revises: 002
Create Date: 2025-10-09 18:49:01.921078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c87e71e8eb12'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to topics (nullable, references Supabase auth.users)
    op.add_column('topics', sa.Column('user_id', sa.UUID(), nullable=True))

    # Add is_system flag (marks default topics vs user-created topics)
    op.add_column('topics', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'))

    # Keywords column already exists in database, skip adding it

    # Mark existing topics as system topics
    op.execute("UPDATE topics SET is_system = true WHERE user_id IS NULL")

    # Add PDF storage fields to papers
    op.add_column('papers', sa.Column('pdf_local_path', sa.String(), nullable=True))
    op.add_column('papers', sa.Column('pdf_downloaded_at', sa.DateTime(timezone=True), nullable=True))

    # Create admin_task_logs table for MVP testing interface
    op.create_table(
        'admin_task_logs',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('task_params', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on task_type and created_at for admin dashboard queries
    op.create_index('ix_admin_task_logs_task_type', 'admin_task_logs', ['task_type'])
    op.create_index('ix_admin_task_logs_created_at', 'admin_task_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_admin_task_logs_created_at', table_name='admin_task_logs')
    op.drop_index('ix_admin_task_logs_task_type', table_name='admin_task_logs')

    # Drop admin_task_logs table
    op.drop_table('admin_task_logs')

    # Remove PDF fields from papers
    op.drop_column('papers', 'pdf_downloaded_at')
    op.drop_column('papers', 'pdf_local_path')

    # Remove topic user support fields
    op.drop_column('topics', 'keywords')
    op.drop_column('topics', 'is_system')
    op.drop_column('topics', 'user_id')
