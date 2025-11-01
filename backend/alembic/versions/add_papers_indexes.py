"""add_papers_indexes

Add database indexes to optimize papers query performance

Revision ID: add_papers_indexes
Revises:
Create Date: 2025-01-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_papers_indexes'
down_revision = 'add_github_scraping'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index on published_date for sorting (most common sort)
    op.create_index(
        'idx_papers_published_date',
        'papers',
        ['published_date'],
        postgresql_using='btree',
        if_not_exists=True
    )

    # Index on year for filtering
    op.create_index(
        'idx_papers_year',
        'papers',
        ['year'],
        if_not_exists=True
    )

    # Index on github_url for has_github filter
    op.create_index(
        'idx_papers_github_url',
        'papers',
        ['github_url'],
        if_not_exists=True
    )

    # Index on paper_topic_matches for topic filtering
    op.create_index(
        'idx_paper_topic_matches_paper_id',
        'paper_topic_matches',
        ['paper_id'],
        if_not_exists=True
    )

    op.create_index(
        'idx_paper_topic_matches_topic_id',
        'paper_topic_matches',
        ['topic_id'],
        if_not_exists=True
    )

    # Composite index for topic + published_date (common query pattern)
    op.create_index(
        'idx_paper_topic_published',
        'paper_topic_matches',
        ['topic_id', 'paper_id'],
        if_not_exists=True
    )

    # Index on github_metrics for sorting by stars
    op.create_index(
        'idx_github_metrics_paper_id',
        'github_metrics',
        ['paper_id'],
        if_not_exists=True
    )

    op.create_index(
        'idx_github_metrics_stars',
        'github_metrics',
        ['current_stars'],
        postgresql_using='btree',
        if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index('idx_github_metrics_stars', table_name='github_metrics', if_exists=True)
    op.drop_index('idx_github_metrics_paper_id', table_name='github_metrics', if_exists=True)
    op.drop_index('idx_paper_topic_published', table_name='paper_topic_matches', if_exists=True)
    op.drop_index('idx_paper_topic_matches_topic_id', table_name='paper_topic_matches', if_exists=True)
    op.drop_index('idx_paper_topic_matches_paper_id', table_name='paper_topic_matches', if_exists=True)
    op.drop_index('idx_papers_github_url', table_name='papers', if_exists=True)
    op.drop_index('idx_papers_year', table_name='papers', if_exists=True)
    op.drop_index('idx_papers_published_date', table_name='papers', if_exists=True)
