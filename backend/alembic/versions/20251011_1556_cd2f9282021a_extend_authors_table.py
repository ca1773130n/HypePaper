"""extend_authors_table

Revision ID: cd2f9282021a
Revises: 21d6fdc6430e
Create Date: 2025-10-11 15:56:53.982866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd2f9282021a'
down_revision: Union[str, None] = '21d6fdc6430e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
