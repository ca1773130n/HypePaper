"""extend_papers_table

Revision ID: cecfd8a87fbf
Revises: 4f6978dd1af8
Create Date: 2025-10-11 15:08:47.024645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cecfd8a87fbf'
down_revision: Union[str, None] = '4f6978dd1af8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to papers table
    op.add_column('papers', sa.Column('vote_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('papers', sa.Column('quick_summary', sa.Text(), nullable=True))
    op.add_column('papers', sa.Column('key_ideas', sa.Text(), nullable=True))
    op.add_column('papers', sa.Column('quantitative_performance', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('papers', sa.Column('qualitative_performance', sa.Text(), nullable=True))

    # Create index on vote_count
    op.create_index('idx_papers_vote_count', 'papers', [sa.text('vote_count DESC')])


def downgrade() -> None:
    op.drop_index('idx_papers_vote_count', 'papers')
    op.drop_column('papers', 'qualitative_performance')
    op.drop_column('papers', 'quantitative_performance')
    op.drop_column('papers', 'key_ideas')
    op.drop_column('papers', 'quick_summary')
    op.drop_column('papers', 'vote_count')
