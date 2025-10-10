"""Paper model for research papers.

Represents papers from arXiv or conference venues with metadata.
Extended with SOTAPapers legacy integration fields.
"""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .author import Author
    from .paper_reference import PaperReference
    from .github_metrics import GitHubMetrics
    from .pdf_content import PDFContent
    from .llm_extraction import LLMExtraction


class Paper(Base):
    """Research paper with SOTAPapers legacy integration.

    Extends base Paper model with:
    - AI-extracted metadata (tasks, methods, datasets, metrics)
    - Conference-specific fields (session_type, accept_status)
    - Citation tracking and bibliography
    - GitHub repository tracking metadata
    """

    __tablename__ = "papers"

    # ============================================================
    # EXISTING FIELDS (from base HypePaper model)
    # ============================================================

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Canonical identifiers
    arxiv_id: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    doi: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )

    # Core metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    published_date: Mapped[date] = mapped_column(nullable=False)
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # URLs
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    arxiv_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ============================================================
    # NEW FIELDS (from SOTAPapers legacy)
    # ============================================================

    # Legacy deterministic ID (title+year hash for duplicate detection)
    legacy_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True,
        comment="SHA256 hash of normalized(title + year) for deduplication"
    )

    # Author affiliations (JSONB for flexible structure)
    affiliations: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Author affiliations: {author_name: [institutions]}"
    )
    affiliations_country: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Country extraction from affiliations: {author_name: [countries]}"
    )

    # Paper metadata
    year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Publication year extracted from published_date"
    )
    pages: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Page range: {start: int, end: int, total: int}"
    )

    # Conference-specific metadata
    paper_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Paper type: 'oral', 'poster', 'spotlight', 'workshop'"
    )
    session_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Conference session category"
    )
    accept_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Acceptance status: 'accepted', 'rejected', 'pending'"
    )

    # Bibliography
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes or annotations"
    )
    bibtex: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="BibTeX citation entry"
    )

    # AI-extracted research tasks (from LLM)
    primary_task: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="Primary research task (e.g., 'Image Classification')"
    )
    secondary_task: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Secondary research task if applicable"
    )
    tertiary_task: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Tertiary research task if applicable"
    )

    # AI-extracted methods
    primary_method: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Primary method used (e.g., 'Convolutional Neural Network')"
    )
    secondary_method: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Secondary method if applicable"
    )
    tertiary_method: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Tertiary method if applicable"
    )

    # AI-extracted datasets and metrics (JSONB arrays)
    datasets_used: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Datasets mentioned: ['ImageNet', 'COCO', ...]"
    )
    metrics_used: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Evaluation metrics: ['Accuracy', 'F1-Score', ...]"
    )

    # AI-extracted comparisons and limitations
    comparisons: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Comparison results: {baseline: score, proposed: score}"
    )
    limitations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Paper limitations extracted by LLM"
    )

    # Additional URLs
    youtube_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="YouTube video URL (presentation/demo)"
    )
    project_page_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Official project page URL"
    )

    # GitHub tracking metadata
    github_star_tracking_start_date: Mapped[Optional[date]] = mapped_column(
        nullable=True,
        comment="Date when star tracking began"
    )
    github_star_tracking_latest_footprint: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Latest tracking snapshot: {date: str, stars: int}"
    )

    # Citation tracking
    citation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Latest citation count from Google Scholar"
    )

    # ============================================================
    # RELATIONSHIPS
    # ============================================================

    # Existing relationships
    metric_snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        "MetricSnapshot",
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    topic_matches: Mapped[list["PaperTopicMatch"]] = relationship(
        "PaperTopicMatch",
        back_populates="paper",
        cascade="all, delete-orphan"
    )

    # New relationships (legacy integration)
    authors_rel: Mapped[list["Author"]] = relationship(
        "Author",
        secondary="paper_authors",
        back_populates="papers"
    )

    citations_out: Mapped[list["PaperReference"]] = relationship(
        "PaperReference",
        foreign_keys="PaperReference.source_paper_id",
        back_populates="source_paper",
        cascade="all, delete-orphan",
        doc="Papers cited by this paper"
    )

    citations_in: Mapped[list["PaperReference"]] = relationship(
        "PaperReference",
        foreign_keys="PaperReference.target_paper_id",
        back_populates="target_paper",
        cascade="all, delete-orphan",
        doc="Papers citing this paper"
    )

    pdf_content: Mapped[Optional["PDFContent"]] = relationship(
        "PDFContent",
        back_populates="paper",
        uselist=False,
        cascade="all, delete-orphan"
    )

    llm_extractions: Mapped[list["LLMExtraction"]] = relationship(
        "LLMExtraction",
        back_populates="paper",
        cascade="all, delete-orphan"
    )

    github_metrics: Mapped[Optional["GitHubMetrics"]] = relationship(
        "GitHubMetrics",
        back_populates="paper",
        uselist=False,
        cascade="all, delete-orphan"
    )

    citation_snapshots: Mapped[list["CitationSnapshot"]] = relationship(
        "CitationSnapshot",
        back_populates="paper",
        cascade="all, delete-orphan",
        doc="Historical citation count snapshots"
    )

    # ============================================================
    # CONSTRAINTS & INDEXES
    # ============================================================

    __table_args__ = (
        # Existing constraints
        CheckConstraint(
            "arxiv_id IS NOT NULL OR doi IS NOT NULL OR legacy_id IS NOT NULL",
            name="at_least_one_id",
        ),
        CheckConstraint(
            "LENGTH(title) >= 10 AND LENGTH(title) <= 500",
            name="title_length_valid",
        ),
        CheckConstraint(
            "array_length(authors, 1) >= 1",
            name="at_least_one_author",
        ),

        # New constraints
        CheckConstraint(
            "paper_type IN ('oral', 'poster', 'spotlight', 'workshop') OR paper_type IS NULL",
            name="paper_type_valid",
        ),
        CheckConstraint(
            "accept_status IN ('accepted', 'rejected', 'pending') OR accept_status IS NULL",
            name="accept_status_valid",
        ),
        CheckConstraint(
            "year >= 1900 AND year <= 2100 OR year IS NULL",
            name="year_valid_range",
        ),

        # Performance indexes
        Index("idx_papers_published_date", "published_date", postgresql_ops={"published_date": "DESC"}),
        Index("idx_papers_year_desc", "year", postgresql_ops={"year": "DESC"}),

        # Full-text search indexes
        Index(
            "idx_papers_title_fts",
            text("to_tsvector('english', title)"),
            postgresql_using="gin",
        ),
        Index(
            "idx_papers_abstract_fts",
            text("to_tsvector('english', abstract)"),
            postgresql_using="gin",
        ),

        # JSONB GIN indexes for containment queries
        Index(
            "idx_papers_affiliations_gin",
            "affiliations",
            postgresql_using="gin",
        ),
        Index(
            "idx_papers_datasets_gin",
            "datasets_used",
            postgresql_using="gin",
        ),
        Index(
            "idx_papers_metrics_gin",
            "metrics_used",
            postgresql_using="gin",
        ),

        # Composite index for filtering
        Index("idx_papers_task_year", "primary_task", "year"),
    )

    # ============================================================
    # COMPUTED PROPERTIES
    # ============================================================

    @property
    def citation_count(self) -> int:
        """Total citations (incoming references)."""
        return len(self.citations_in)

    @property
    def reference_count(self) -> int:
        """Total references (outgoing citations)."""
        return len(self.citations_out)

    @property
    def has_github(self) -> bool:
        """Check if paper has associated GitHub repository."""
        return self.github_url is not None and self.github_metrics is not None

    @property
    def github_stars(self) -> Optional[int]:
        """Current GitHub star count."""
        if self.github_metrics:
            return self.github_metrics.current_stars
        return None

    def __repr__(self) -> str:
        """String representation."""
        identifier = self.arxiv_id or self.doi or self.legacy_id or str(self.id)
        return f"<Paper({identifier}): {self.title[:50]}...>"
