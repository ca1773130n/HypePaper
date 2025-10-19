"""extend_metric_snapshots_table

Revision ID: 7700b3b065ce
Revises: b73c18bef753
Create Date: 2025-10-11 15:08:47.618879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7700b3b065ce'
down_revision: Union[str, None] = 'b73c18bef753'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to metric_snapshots table
    op.add_column('metric_snapshots', sa.Column('vote_count', sa.Integer(), nullable=True))
    op.add_column('metric_snapshots', sa.Column('hype_score', sa.Float(), nullable=True))

    # Add check constraint for hype_score
    op.create_check_constraint('hype_score_non_negative', 'metric_snapshots', 'hype_score IS NULL OR hype_score >= 0')


def downgrade() -> None:
    op.drop_constraint('hype_score_non_negative', 'metric_snapshots', type_='check')
    op.drop_column('metric_snapshots', 'hype_score')
    op.drop_column('metric_snapshots', 'vote_count')
