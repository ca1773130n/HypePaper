"""add legacy fields and new tables for SOTAPapers integration

Revision ID: 002
Revises: 001
Create Date: 2025-10-08

Extends papers table with 22 legacy fields and creates 6 new tables:
- authors: Paper authors with affiliations
- paper_authors: Junction table for papers <-> authors
- paper_references: Citation relationships (bidirectional)
- github_metrics: GitHub metrics (one-to-one with papers)
- github_star_snapshots: Daily star snapshots (TimescaleDB hypertable)
- pdf_content: PDF text and table extraction results
- llm_extractions: AI-extracted metadata with verification
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Extend papers table and create new tables."""

    # ============================================================
    # 1. EXTEND PAPERS TABLE WITH 22 LEGACY FIELDS
    # ============================================================

    # Add legacy ID for duplicate detection
    op.add_column("papers", sa.Column("legacy_id", sa.String(50), nullable=True))
    op.create_index("idx_papers_legacy_id", "papers", ["legacy_id"], unique=True)

    # Add year column (extracted from published_date)
    op.add_column("papers", sa.Column("year", sa.Integer(), nullable=True))
    op.create_index("idx_papers_year", "papers", ["year"], postgresql_ops={"year": "DESC"})
    op.execute(sa.text("UPDATE papers SET year = EXTRACT(YEAR FROM published_date)"))

    # Conference/publication metadata
    op.add_column("papers", sa.Column("paper_type", sa.String(50), nullable=True))  # 'oral', 'poster', 'spotlight', 'workshop'
    op.add_column("papers", sa.Column("session_type", sa.String(100), nullable=True))
    op.add_column("papers", sa.Column("accept_status", sa.String(50), nullable=True))  # 'accepted', 'rejected', 'pending'
    op.add_column("papers", sa.Column("note", sa.Text(), nullable=True))
    op.add_column("papers", sa.Column("pages", postgresql.JSONB(), nullable=True))

    # Author metadata
    op.add_column("papers", sa.Column("affiliations", postgresql.JSONB(), nullable=True))
    op.add_column("papers", sa.Column("affiliations_country", postgresql.JSONB(), nullable=True))

    # Bibliography
    op.add_column("papers", sa.Column("bibtex", sa.Text(), nullable=True))

    # AI-extracted research metadata
    op.add_column("papers", sa.Column("primary_task", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("secondary_task", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("tertiary_task", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("primary_method", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("secondary_method", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("tertiary_method", sa.String(200), nullable=True))
    op.add_column("papers", sa.Column("datasets_used", postgresql.JSONB(), nullable=True))
    op.add_column("papers", sa.Column("metrics_used", postgresql.JSONB(), nullable=True))
    op.add_column("papers", sa.Column("comparisons", postgresql.JSONB(), nullable=True))
    op.add_column("papers", sa.Column("limitations", sa.Text(), nullable=True))

    # Additional media URLs
    op.add_column("papers", sa.Column("youtube_url", sa.String(500), nullable=True))
    op.add_column("papers", sa.Column("project_page_url", sa.String(500), nullable=True))

    # GitHub metrics (from legacy)
    op.add_column("papers", sa.Column("github_star_count", sa.Integer(), nullable=True))
    op.add_column("papers", sa.Column("github_star_avg_hype", sa.Float(), nullable=True))
    op.add_column("papers", sa.Column("github_star_weekly_hype", sa.Float(), nullable=True))
    op.add_column("papers", sa.Column("github_star_monthly_hype", sa.Float(), nullable=True))
    op.add_column("papers", sa.Column("github_star_tracking_start_date", sa.String(50), nullable=True))
    op.add_column("papers", sa.Column("github_star_tracking_latest_footprint", postgresql.JSONB(), nullable=True))

    # Citation count (from legacy)
    op.add_column("papers", sa.Column("citations_total", sa.Integer(), nullable=True, server_default="0"))

    # Create GIN indexes for JSONB fields
    op.create_index("idx_papers_affiliations_gin", "papers", ["affiliations"], postgresql_using="gin")
    op.create_index("idx_papers_datasets_used_gin", "papers", ["datasets_used"], postgresql_using="gin")
    op.create_index("idx_papers_metrics_used_gin", "papers", ["metrics_used"], postgresql_using="gin")

    # Create index for primary_task filtering
    op.create_index("idx_papers_primary_task", "papers", ["primary_task"])
    op.create_index("idx_papers_task_year", "papers", ["primary_task", "year"])

    # ============================================================
    # 2. CREATE AUTHORS TABLE
    # ============================================================

    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("affiliations", postgresql.JSONB(), nullable=True),
        sa.Column("countries", postgresql.JSONB(), nullable=True),
        sa.Column("paper_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("name", name="uq_authors_name"),
    )
    op.create_index("idx_authors_name", "authors", ["name"])
    op.create_index("idx_authors_affiliations_gin", "authors", ["affiliations"], postgresql_using="gin")
    op.execute(
        sa.text(
            "CREATE INDEX idx_authors_name_fts ON authors USING gin(to_tsvector('english', name))"
        )
    )

    # ============================================================
    # 3. CREATE PAPER_AUTHORS JUNCTION TABLE
    # ============================================================

    op.create_table(
        "paper_authors",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("affiliation_snapshot", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("paper_id", "author_id", name="pk_paper_authors"),
        sa.CheckConstraint("position >= 1", name="author_position_positive"),
    )
    op.create_index("idx_paper_authors_paper", "paper_authors", ["paper_id"])
    op.create_index("idx_paper_authors_author", "paper_authors", ["author_id"])

    # ============================================================
    # 4. CREATE PAPER_REFERENCES TABLE (CITATIONS)
    # ============================================================

    op.create_table(
        "paper_references",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_text", sa.Text(), nullable=True),
        sa.Column("match_quality", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reference_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("paper_id", "reference_id", name="pk_paper_references"),
        sa.CheckConstraint("match_quality IS NULL OR (match_quality >= 0 AND match_quality <= 100)", name="match_quality_range"),
    )
    op.create_index("idx_paper_references_paper", "paper_references", ["paper_id"])
    op.create_index("idx_paper_references_reference", "paper_references", ["reference_id"])

    # ============================================================
    # 5. CREATE GITHUB_METRICS TABLE (ONE-TO-ONE WITH PAPER)
    # ============================================================

    op.create_table(
        "github_metrics",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_url", sa.String(500), nullable=False, unique=True),
        sa.Column("repository_owner", sa.String(100), nullable=False),
        sa.Column("repository_name", sa.String(200), nullable=False),
        sa.Column("current_stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_forks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_watchers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_language", sa.String(50), nullable=True),
        sa.Column("repository_description", sa.Text(), nullable=True),
        sa.Column("repository_created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("repository_updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("average_hype", sa.Float(), nullable=True),
        sa.Column("weekly_hype", sa.Float(), nullable=True),
        sa.Column("monthly_hype", sa.Float(), nullable=True),
        sa.Column("tracking_start_date", sa.Date(), nullable=False),
        sa.Column("last_tracked_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("tracking_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_github_metrics_repo_url", "github_metrics", ["repository_url"])
    op.create_index("idx_github_metrics_owner", "github_metrics", ["repository_owner"])
    op.create_index("idx_github_metrics_stars", "github_metrics", ["current_stars"], postgresql_ops={"current_stars": "DESC"})
    op.create_index("idx_github_metrics_weekly_hype", "github_metrics", ["weekly_hype"], postgresql_ops={"weekly_hype": "DESC"})
    op.create_index("idx_github_metrics_monthly_hype", "github_metrics", ["monthly_hype"], postgresql_ops={"monthly_hype": "DESC"})

    # ============================================================
    # 6. CREATE GITHUB_STAR_SNAPSHOTS TABLE (TIMESCALEDB HYPERTABLE)
    # ============================================================

    op.create_table(
        "github_star_snapshots",
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("star_count", sa.Integer(), nullable=False),
        sa.Column("fork_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watcher_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stars_gained_since_yesterday", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("paper_id", "snapshot_date", name="pk_github_star_snapshots"),
        sa.ForeignKeyConstraint(["paper_id"], ["github_metrics.paper_id"], ondelete="CASCADE"),
    )
    op.create_index("idx_star_snapshots_date", "github_star_snapshots", ["snapshot_date"], postgresql_ops={"snapshot_date": "DESC"})
    op.create_index("idx_star_snapshots_paper_date", "github_star_snapshots", ["paper_id", "snapshot_date"])

    # Convert to TimescaleDB hypertable (use snapshot_date as partitioning column)
    op.execute(
        sa.text(
            "SELECT create_hypertable('github_star_snapshots', 'snapshot_date', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
        )
    )

    # Enable compression after 30 days
    op.execute(
        sa.text(
            """
            ALTER TABLE github_star_snapshots SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'paper_id'
            )
            """
        )
    )
    op.execute(
        sa.text(
            "SELECT add_compression_policy('github_star_snapshots', INTERVAL '30 days', if_not_exists => TRUE)"
        )
    )

    # ============================================================
    # 7. CREATE PDF_CONTENT TABLE
    # ============================================================

    op.create_table(
        "pdf_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("table_csv_paths", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("parsed_references", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("extraction_timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("paper_id", name="uq_pdf_content_paper"),
    )
    op.create_index("idx_pdf_content_paper", "pdf_content", ["paper_id"])
    op.execute(
        sa.text(
            "CREATE INDEX idx_pdf_content_full_text_fts ON pdf_content USING gin(to_tsvector('english', full_text))"
        )
    )

    # ============================================================
    # 8. CREATE LLM_EXTRACTIONS TABLE
    # ============================================================

    op.create_table(
        "llm_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extraction_type", sa.String(50), nullable=False),  # 'task', 'method', 'dataset', 'metric', 'limitation'
        sa.Column("extracted_values", postgresql.JSONB(), nullable=False),
        sa.Column("llm_model", sa.String(100), nullable=False),
        sa.Column("extraction_timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("verification_status", sa.String(50), nullable=False, server_default="'pending_review'"),  # 'pending_review', 'verified', 'rejected'
        sa.Column("verified_by", sa.String(200), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "extraction_type IN ('task', 'method', 'dataset', 'metric', 'limitation', 'comparison')",
            name="extraction_type_valid"
        ),
        sa.CheckConstraint(
            "verification_status IN ('pending_review', 'verified', 'rejected')",
            name="verification_status_valid"
        ),
    )
    op.create_index("idx_llm_extractions_paper", "llm_extractions", ["paper_id"])
    op.create_index("idx_llm_extractions_type", "llm_extractions", ["extraction_type"])
    op.create_index("idx_llm_extractions_status", "llm_extractions", ["verification_status"])
    op.create_index("idx_llm_extractions_paper_type", "llm_extractions", ["paper_id", "extraction_type"])


def downgrade() -> None:
    """Remove legacy fields and new tables."""

    # Drop new tables
    op.drop_table("llm_extractions")
    op.drop_table("pdf_content")
    op.drop_table("github_star_snapshots")
    op.drop_table("github_metrics")
    op.drop_table("paper_references")
    op.drop_table("paper_authors")
    op.drop_table("authors")

    # Drop indexes on papers
    op.drop_index("idx_papers_task_year", "papers")
    op.drop_index("idx_papers_primary_task", "papers")
    op.drop_index("idx_papers_metrics_used_gin", "papers")
    op.drop_index("idx_papers_datasets_used_gin", "papers")
    op.drop_index("idx_papers_affiliations_gin", "papers")
    op.drop_index("idx_papers_year", "papers")
    op.drop_index("idx_papers_legacy_id", "papers")

    # Drop legacy columns from papers
    op.drop_column("papers", "citations_total")
    op.drop_column("papers", "github_star_tracking_latest_footprint")
    op.drop_column("papers", "github_star_tracking_start_date")
    op.drop_column("papers", "github_star_monthly_hype")
    op.drop_column("papers", "github_star_weekly_hype")
    op.drop_column("papers", "github_star_avg_hype")
    op.drop_column("papers", "github_star_count")
    op.drop_column("papers", "project_page_url")
    op.drop_column("papers", "youtube_url")
    op.drop_column("papers", "limitations")
    op.drop_column("papers", "comparisons")
    op.drop_column("papers", "metrics_used")
    op.drop_column("papers", "datasets_used")
    op.drop_column("papers", "tertiary_method")
    op.drop_column("papers", "secondary_method")
    op.drop_column("papers", "primary_method")
    op.drop_column("papers", "tertiary_task")
    op.drop_column("papers", "secondary_task")
    op.drop_column("papers", "primary_task")
    op.drop_column("papers", "bibtex")
    op.drop_column("papers", "affiliations_country")
    op.drop_column("papers", "affiliations")
    op.drop_column("papers", "pages")
    op.drop_column("papers", "note")
    op.drop_column("papers", "accept_status")
    op.drop_column("papers", "session_type")
    op.drop_column("papers", "paper_type")
    op.drop_column("papers", "year")
    op.drop_column("papers", "legacy_id")
