"""add_vote_count_trigger

Revision ID: 82c264fc6553
Revises: 0e0fb7c16085
Create Date: 2025-10-11 15:56:54.459212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82c264fc6553'
down_revision: Union[str, None] = '0e0fb7c16085'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
