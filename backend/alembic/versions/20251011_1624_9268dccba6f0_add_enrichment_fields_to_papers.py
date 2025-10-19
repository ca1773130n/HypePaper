"""add_enrichment_fields_to_papers

Revision ID: 9268dccba6f0
Revises: 82c264fc6553
Create Date: 2025-10-11 16:24:50.248468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9268dccba6f0'
down_revision: Union[str, None] = '82c264fc6553'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add enrichment fields that are missing from papers table
    # quick_summary, key_ideas, quantitative_performance, qualitative_performance already exist
    # Only limitations needs to be checked (it's defined in model line 196)

    # Check which columns already exist and only add missing ones
    # These fields were added in model but may not exist in DB yet
    from sqlalchemy.dialects.postgresql import JSONB

    # Note: Most of these fields already exist from earlier migrations
    # This migration ensures they're all present

    # Execute raw SQL to check and add if not exists
    op.execute("""
        DO $$
        BEGIN
            -- Add quick_summary if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='papers' AND column_name='quick_summary') THEN
                ALTER TABLE papers ADD COLUMN quick_summary TEXT;
                COMMENT ON COLUMN papers.quick_summary IS 'Brief paper summary (1-2 sentences)';
            END IF;

            -- Add key_ideas if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='papers' AND column_name='key_ideas') THEN
                ALTER TABLE papers ADD COLUMN key_ideas TEXT;
                COMMENT ON COLUMN papers.key_ideas IS 'Main contributions and key ideas';
            END IF;

            -- Add quantitative_performance if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='papers' AND column_name='quantitative_performance') THEN
                ALTER TABLE papers ADD COLUMN quantitative_performance JSONB;
                COMMENT ON COLUMN papers.quantitative_performance IS 'Numerical results: {metric: value, baseline: value}';
            END IF;

            -- Add qualitative_performance if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='papers' AND column_name='qualitative_performance') THEN
                ALTER TABLE papers ADD COLUMN qualitative_performance TEXT;
                COMMENT ON COLUMN papers.qualitative_performance IS 'Descriptive performance results';
            END IF;

            -- Add limitations if not exists (redundant check, may already exist)
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='papers' AND column_name='limitations') THEN
                ALTER TABLE papers ADD COLUMN limitations TEXT;
                COMMENT ON COLUMN papers.limitations IS 'Paper limitations extracted by LLM';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop enrichment fields
    op.execute("""
        ALTER TABLE papers
        DROP COLUMN IF EXISTS quick_summary,
        DROP COLUMN IF EXISTS key_ideas,
        DROP COLUMN IF EXISTS quantitative_performance,
        DROP COLUMN IF EXISTS qualitative_performance;
        -- Note: Keep limitations as it's used elsewhere
    """)
