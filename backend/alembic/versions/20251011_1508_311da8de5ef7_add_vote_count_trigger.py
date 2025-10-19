"""add_vote_count_trigger

Revision ID: 311da8de5ef7
Revises: 7700b3b065ce
Create Date: 2025-10-11 15:08:47.906154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '311da8de5ef7'
down_revision: Union[str, None] = '7700b3b065ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create function to update paper vote_count
    op.execute("""
        CREATE OR REPLACE FUNCTION update_paper_vote_count()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE papers
            SET vote_count = (
                SELECT COALESCE(SUM(CASE WHEN vote_type = 'upvote' THEN 1 ELSE -1 END), 0)
                FROM votes
                WHERE paper_id = COALESCE(NEW.paper_id, OLD.paper_id)
            )
            WHERE id = COALESCE(NEW.paper_id, OLD.paper_id);
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger on votes table
    op.execute("""
        CREATE TRIGGER vote_count_trigger
        AFTER INSERT OR UPDATE OR DELETE ON votes
        FOR EACH ROW EXECUTE FUNCTION update_paper_vote_count();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS vote_count_trigger ON votes")
    op.execute("DROP FUNCTION IF EXISTS update_paper_vote_count()")
