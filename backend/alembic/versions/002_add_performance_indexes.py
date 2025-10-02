"""add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-10-02

Add database indexes for common query patterns to improve performance.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes."""

    # Papers table indexes for common queries
    op.create_index(
        "idx_papers_published_date",
        "papers",
        ["published_date"],
        postgresql_using="btree",
        postgresql_ops={"published_date": "DESC"},
    )
    op.create_index(
        "idx_papers_arxiv_id",
        "papers",
        ["arxiv_id"],
        unique=True,
        postgresql_where=sa.text("arxiv_id IS NOT NULL"),
    )
    op.create_index(
        "idx_papers_doi",
        "papers",
        ["doi"],
        unique=True,
        postgresql_where=sa.text("doi IS NOT NULL"),
    )

    # Metric snapshots indexes for time-series queries
    op.create_index(
        "idx_metric_snapshots_date_desc",
        "metric_snapshots",
        ["snapshot_date"],
        postgresql_using="btree",
        postgresql_ops={"snapshot_date": "DESC"},
    )
    op.create_index(
        "idx_metric_snapshots_paper_date",
        "metric_snapshots",
        ["paper_id", "snapshot_date"],
        postgresql_ops={"snapshot_date": "DESC"},
    )

    # Topics table index for search
    op.create_index(
        "idx_topics_name",
        "topics",
        ["name"],
        postgresql_using="btree",
    )

    # Composite index for paper listing queries (most common query pattern)
    # Supports: SELECT papers WHERE topic_id = X ORDER BY published_date DESC
    op.execute(
        sa.text(
            """
            CREATE INDEX idx_papers_composite_query
            ON papers (id, published_date DESC, github_url)
            WHERE github_url IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("idx_papers_composite_query", table_name="papers")
    op.drop_index("idx_topics_name", table_name="topics")
    op.drop_index("idx_metric_snapshots_paper_date", table_name="metric_snapshots")
    op.drop_index("idx_metric_snapshots_date_desc", table_name="metric_snapshots")
    op.drop_index("idx_papers_doi", table_name="papers")
    op.drop_index("idx_papers_arxiv_id", table_name="papers")
    op.drop_index("idx_papers_published_date", table_name="papers")
