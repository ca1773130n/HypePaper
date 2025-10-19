"""add_votes_table

Revision ID: 3762a4220dea
Revises: 311da8de5ef7
Create Date: 2025-10-11 15:56:47.047542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3762a4220dea'
down_revision: Union[str, None] = '311da8de5ef7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
