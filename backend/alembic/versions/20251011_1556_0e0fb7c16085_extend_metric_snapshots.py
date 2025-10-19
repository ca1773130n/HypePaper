"""extend_metric_snapshots

Revision ID: 0e0fb7c16085
Revises: cd2f9282021a
Create Date: 2025-10-11 15:56:54.262314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e0fb7c16085'
down_revision: Union[str, None] = 'cd2f9282021a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
