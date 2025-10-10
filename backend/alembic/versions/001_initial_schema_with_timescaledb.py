"""initial schema with timescaledb

Revision ID: 001
Revises:
Create Date: 2025-10-02

Creates tables for papers, topics, metric_snapshots (TimescaleDB hypertable),
and paper_topic_matches with all constraints and indexes.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables and TimescaleDB hypertable."""

    # 1. Papers table (with enhanced fields for PDF, references, and SOTAPapers)
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("arxiv_id", sa.String(20), nullable=True),
        sa.Column("doi", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("authors", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("published_date", sa.Date(), nullable=False),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("arxiv_url", sa.String(500), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("pdf_local_path", sa.String(1000), nullable=True),
        sa.Column("reference_count", sa.Integer(), nullable=True),
        sa.Column("references_extracted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sotapapers_id", sa.String(100), nullable=True),
        sa.Column("sotapapers_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("arxiv_id IS NOT NULL OR doi IS NOT NULL", name="at_least_one_id"),
        sa.CheckConstraint("LENGTH(title) >= 10 AND LENGTH(title) <= 500", name="title_length_valid"),
        sa.CheckConstraint("array_length(authors, 1) >= 1", name="at_least_one_author"),
        sa.UniqueConstraint("arxiv_id", name="uq_papers_arxiv_id"),
        sa.UniqueConstraint("doi", name="uq_papers_doi"),
        sa.UniqueConstraint("sotapapers_id", name="uq_papers_sotapapers_id"),
    )
    op.create_index("idx_papers_arxiv_id", "papers", ["arxiv_id"])
    op.create_index("idx_papers_doi", "papers", ["doi"])
    op.create_index("idx_papers_published_date", "papers", ["published_date"], postgresql_ops={"published_date": "DESC"})
    op.create_index("idx_papers_sotapapers_id", "papers", ["sotapapers_id"])
    op.execute(
        sa.text(
            "CREATE INDEX idx_papers_title_fts ON papers USING gin(to_tsvector('english', title))"
        )
    )

    # 2. Topics table (with user management support)
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("LENGTH(name) >= 3 AND LENGTH(name) <= 100", name="topic_name_length_valid"),
        sa.CheckConstraint("name = LOWER(name)", name="topic_name_lowercase"),
        sa.CheckConstraint("name ~ '^[a-z0-9 -]+$'", name="topic_name_format_valid"),
        sa.UniqueConstraint("name", name="uq_topics_name"),
    )
    op.create_index("idx_topics_user_id", "topics", ["user_id"])
    op.create_index("idx_topics_is_system", "topics", ["is_system"])

    # 3. Metric snapshots table (regular PostgreSQL table with time-series optimizations)
    op.create_table(
        "metric_snapshots",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("github_stars", sa.Integer(), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.CheckConstraint("github_stars IS NULL OR github_stars >= 0", name="github_stars_non_negative"),
        sa.CheckConstraint("citation_count IS NULL OR citation_count >= 0", name="citation_count_non_negative"),
        sa.PrimaryKeyConstraint("paper_id", "snapshot_date", name="pk_metric_snapshots"),
    )
    # Create indexes for efficient time-series queries
    op.create_index("idx_metric_snapshots_paper_id", "metric_snapshots", ["paper_id"])
    op.create_index(
        "idx_metric_snapshots_date",
        "metric_snapshots",
        ["snapshot_date"],
        postgresql_ops={"snapshot_date": "DESC"}
    )
    op.create_index(
        "idx_metric_snapshots_paper_date",
        "metric_snapshots",
        ["paper_id", "snapshot_date"],
        postgresql_ops={"snapshot_date": "DESC"}
    )

    # 4. Paper-Topic matches table
    op.create_table(
        "paper_topic_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("matched_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("matched_by", sa.String(20), nullable=False, server_default=sa.text("'llm'")),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.CheckConstraint("relevance_score >= 0.0 AND relevance_score <= 10.0", name="relevance_score_range"),
        sa.CheckConstraint("relevance_score >= 6.0", name="relevance_score_threshold"),
        sa.CheckConstraint("matched_by IN ('llm', 'manual')", name="matched_by_valid_values"),
        sa.UniqueConstraint("paper_id", "topic_id", name="unique_paper_topic_pair"),
    )
    op.create_index("idx_paper_topic_matches_paper", "paper_topic_matches", ["paper_id"])
    op.create_index(
        "idx_paper_topic_matches_topic",
        "paper_topic_matches",
        ["topic_id", "relevance_score"],
        postgresql_ops={"relevance_score": "DESC"},
    )

    # 5. Hype scores table
    op.create_table(
        "hype_scores",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("star_growth_score", sa.Float(), nullable=True),
        sa.Column("citation_growth_score", sa.Float(), nullable=True),
        sa.Column("absolute_score", sa.Float(), nullable=True),
        sa.Column("recency_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("paper_id", "score_date", name="pk_hype_scores"),
    )
    op.create_index("idx_hype_scores_paper_id", "hype_scores", ["paper_id"])
    op.create_index(
        "idx_hype_scores_date",
        "hype_scores",
        ["score_date"],
        postgresql_ops={"score_date": "DESC"}
    )

    # 6. Paper references table (citation graph)
    op.create_table(
        "paper_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_paper_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_title", sa.String(500), nullable=False),
        sa.Column("target_authors", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("target_year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["source_paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("source_paper_id", "target_title", name="unique_source_target_pair"),
    )
    op.create_index("idx_paper_references_source", "paper_references", ["source_paper_id"])
    op.create_index("idx_paper_references_target", "paper_references", ["target_paper_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("paper_references")
    op.drop_table("hype_scores")
    op.drop_table("paper_topic_matches")
    op.drop_table("metric_snapshots")
    op.drop_table("topics")
    op.drop_table("papers")
