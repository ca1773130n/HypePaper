"""add github scraping fields

Revision ID: add_github_scraping
Revises: 9268dccba6f0
Create Date: 2025-10-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_github_scraping'
down_revision: Union[str, None] = '9268dccba6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add GitHub stars scraped field to papers table
    # Note: github_url already exists in the schema
    op.add_column('papers', sa.Column('github_stars_scraped', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove GitHub scraping field
    op.drop_column('papers', 'github_stars_scraped')