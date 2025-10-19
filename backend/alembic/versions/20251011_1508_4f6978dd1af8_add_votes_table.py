"""add_votes_table

Revision ID: 4f6978dd1af8
Revises: b67a24b16366
Create Date: 2025-10-11 15:08:38.376121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f6978dd1af8'
down_revision: Union[str, None] = 'b67a24b16366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vote_type enum
    op.execute("CREATE TYPE vote_type_enum AS ENUM ('upvote', 'downvote')")

    # Create votes table
    op.create_table(
        'votes',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vote_type', sa.Enum('upvote', 'downvote', name='vote_type_enum'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'paper_id'),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('idx_votes_paper', 'votes', ['paper_id'])
    op.create_index('idx_votes_user', 'votes', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_votes_user', 'votes')
    op.drop_index('idx_votes_paper', 'votes')
    op.drop_table('votes')
    op.execute("DROP TYPE vote_type_enum")
