"""extend_papers_table

Revision ID: 21d6fdc6430e
Revises: 3762a4220dea
Create Date: 2025-10-11 15:56:53.793109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21d6fdc6430e'
down_revision: Union[str, None] = '3762a4220dea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
