"""extend_authors_table

Revision ID: b73c18bef753
Revises: cecfd8a87fbf
Create Date: 2025-10-11 15:08:47.322589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b73c18bef753'
down_revision: Union[str, None] = 'cecfd8a87fbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraint on name (if exists)
    op.execute("ALTER TABLE authors DROP CONSTRAINT IF EXISTS authors_name_key")

    # Add new columns
    op.add_column('authors', sa.Column('total_citation_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('authors', sa.Column('latest_paper_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('authors', sa.Column('email', sa.String(200), nullable=True))
    op.add_column('authors', sa.Column('website_url', sa.String(500), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key('fk_authors_latest_paper', 'authors', 'papers', ['latest_paper_id'], ['id'], ondelete='SET NULL')

    # Create indexes
    op.create_index('idx_authors_citation_count', 'authors', [sa.text('total_citation_count DESC')])
    op.create_index('idx_authors_paper_count', 'authors', [sa.text('paper_count DESC')])


def downgrade() -> None:
    op.drop_index('idx_authors_paper_count', 'authors')
    op.drop_index('idx_authors_citation_count', 'authors')
    op.drop_constraint('fk_authors_latest_paper', 'authors', type_='foreignkey')
    op.drop_column('authors', 'website_url')
    op.drop_column('authors', 'email')
    op.drop_column('authors', 'latest_paper_id')
    op.drop_column('authors', 'total_citation_count')
    # Re-add unique constraint on name
    op.create_unique_constraint('authors_name_key', 'authors', ['name'])
