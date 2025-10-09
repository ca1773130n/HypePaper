# Data Model: SOTAPapers Legacy Integration

**Feature**: 002-convert-the-integration | **Date**: 2025-10-08
**Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Overview

This document defines the extended data model for integrating SOTAPapers legacy features into HypePaper. The model extends the existing `Paper` entity with 22 new fields from the legacy codebase (37 total legacy fields, 15 already exist) and introduces 5 new entities for citations, GitHub tracking, PDF content, LLM extractions, and authors.

**Key Design Decisions**:
- PostgreSQL-native features: JSONB for flexible arrays, GIN indexes for fast containment queries
- Deterministic Paper IDs: Hash-based IDs from title+year for duplicate detection
- Bidirectional citations: Junction table with reference text preservation
- Time-series GitHub metrics: TimescaleDB for efficient star tracking history
- Async-first: All models support SQLAlchemy async operations

## Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│      Author         │◄────────┤   PaperAuthor       │
│                     │ many    │   (junction)        │
└─────────────────────┘         └──────┬──────────────┘
                                        │ many
                                        ▼
┌─────────────────────┐         ┌─────────────────────┐
│   GitHubMetrics     │────────►│      Paper          │
│   (time-series)     │ one     │   (37 fields)       │
└─────────────────────┘         └──────┬──────────────┘
                                        │
                      ┌─────────────────┼─────────────────┐
                      │                 │                 │
                      ▼                 ▼                 ▼
            ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
            │  PaperReference │ │ PDFContent  │ │LLMExtraction│
            │  (citations)    │ │             │ │             │
            └─────────────────┘ └─────────────┘ └─────────────┘
                      │
                      │ self-referential
                      ▼
            ┌─────────────────┐
            │  Paper (cited)  │
            └─────────────────┘
```

## Entities

### 1. Paper (Extended)

Core entity representing academic papers with comprehensive metadata from multiple sources.

**Table Name**: `papers`

**Extended Fields** (22 new fields added to existing 15):

```python
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, String, Text, text, Integer
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


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
        foreign_keys="PaperReference.paper_id",
        back_populates="paper",
        cascade="all, delete-orphan",
        doc="Papers cited by this paper"
    )

    citations_in: Mapped[list["PaperReference"]] = relationship(
        "PaperReference",
        foreign_keys="PaperReference.reference_id",
        back_populates="referenced_paper",
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
```

**Validation Rules**:
1. At least one ID required: `arxiv_id`, `doi`, or `legacy_id`
2. Title: 10-500 characters
3. Authors: At least 1 author
4. Paper type: Must be one of `['oral', 'poster', 'spotlight', 'workshop']` or NULL
5. Accept status: Must be one of `['accepted', 'rejected', 'pending']` or NULL
6. Year: 1900-2100 range

**Performance Optimizations**:
- GIN indexes on JSONB fields (`affiliations`, `datasets_used`, `metrics_used`) for fast containment queries
- Full-text search indexes on `title` and `abstract`
- Composite index on `(primary_task, year)` for filtered queries
- Descending index on `year` for recent papers first

---

### 2. Author

Represents paper authors with affiliation tracking across multiple papers.

**Table Name**: `authors`

```python
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Author(Base):
    """Paper author with affiliation tracking.

    Many-to-many relationship with papers via paper_authors junction table.
    """

    __tablename__ = "authors"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Author identity
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Full author name (normalized)"
    )

    # Affiliations across all papers
    affiliations: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of institutions: ['MIT', 'Stanford', ...]"
    )

    countries: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of countries: ['USA', 'UK', ...]"
    )

    # Statistics
    paper_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Total papers authored"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    papers: Mapped[list["Paper"]] = relationship(
        "Paper",
        secondary="paper_authors",
        back_populates="authors_rel"
    )

    __table_args__ = (
        Index(
            "idx_authors_name_fts",
            text("to_tsvector('english', name)"),
            postgresql_using="gin",
        ),
        Index(
            "idx_authors_affiliations_gin",
            "affiliations",
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<Author({self.name}): {self.paper_count} papers>"


# Junction table for many-to-many Paper <-> Author
class PaperAuthor(Base):
    """Junction table linking papers and authors."""

    __tablename__ = "paper_authors"

    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True
    )

    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("authors.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Author position in paper (1 = first author)
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Author position (1 = first author)"
    )

    # Affiliation at time of this paper
    affiliation_snapshot: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Author affiliation for this specific paper"
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )

    __table_args__ = (
        Index("idx_paper_authors_paper", "paper_id"),
        Index("idx_paper_authors_author", "author_id"),
    )
```

**Validation Rules**:
1. Author name must be unique (normalized)
2. Position must be >= 1
3. Paper count automatically updated via trigger

---

### 3. PaperReference (Citation)

Bidirectional citation relationships between papers with original reference text preservation.

**Table Name**: `paper_references`

```python
from sqlalchemy import ForeignKey, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PaperReference(Base):
    """Citation relationship between papers (bidirectional).

    Represents: Paper A cites Paper B
    - paper_id: Source paper (A)
    - reference_id: Cited paper (B)
    """

    __tablename__ = "paper_references"

    # Composite primary key
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Paper containing the citation"
    )

    reference_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Paper being cited"
    )

    # Original citation text from PDF
    reference_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original citation string from PDF References section"
    )

    # Fuzzy matching metadata
    match_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Levenshtein similarity score (0-100)"
    )

    match_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Matching method: 'exact', 'fuzzy_title', 'fuzzy_title_year'"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Manual verification timestamp"
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[paper_id],
        back_populates="citations_out"
    )

    referenced_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[reference_id],
        back_populates="citations_in"
    )

    __table_args__ = (
        CheckConstraint(
            "paper_id != reference_id",
            name="no_self_citation"
        ),
        CheckConstraint(
            "match_score >= 0 AND match_score <= 100 OR match_score IS NULL",
            name="match_score_valid_range"
        ),
        Index("idx_citations_paper", "paper_id"),
        Index("idx_citations_reference", "reference_id"),
        Index("idx_citations_match_score", "match_score", postgresql_ops={"match_score": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Citation({self.paper_id} -> {self.reference_id}, score={self.match_score})>"
```

**Validation Rules**:
1. No self-citations: `paper_id != reference_id`
2. Match score: 0-100 range or NULL
3. Match method: One of `['exact', 'fuzzy_title', 'fuzzy_title_year']` or NULL

**Query Patterns**:
```python
# Find all papers cited by paper X
cited_papers = (
    session.query(Paper)
    .join(PaperReference, PaperReference.reference_id == Paper.id)
    .filter(PaperReference.paper_id == paper_x_id)
    .all()
)

# Find all papers citing paper X
citing_papers = (
    session.query(Paper)
    .join(PaperReference, PaperReference.paper_id == Paper.id)
    .filter(PaperReference.reference_id == paper_x_id)
    .all()
)

# Citation graph traversal (depth-first)
def get_citation_tree(paper_id, depth=2):
    """Get citation tree up to specified depth."""
    # Recursive CTE query (see quickstart.md for full implementation)
```

---

### 4. GitHubMetrics

Time-series tracking of GitHub repository metrics with TimescaleDB.

**Table Name**: `github_metrics`

```python
from sqlalchemy import ForeignKey, String, Integer, Float, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GitHubMetrics(Base):
    """GitHub repository metrics for papers.

    One-to-one relationship with Paper.
    Stores time-series star tracking data using TimescaleDB hypertable.
    """

    __tablename__ = "github_metrics"

    # Primary key (also foreign key)
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Repository identification
    repository_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="GitHub repository URL"
    )

    repository_owner: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Repository owner (user/org)"
    )

    repository_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Repository name"
    )

    # Current snapshot
    current_stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        index=True,
        comment="Current star count"
    )

    current_forks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Current fork count"
    )

    current_watchers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Current watcher count"
    )

    # Repository metadata
    primary_language: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Primary programming language"
    )

    repository_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Repository description"
    )

    repository_created_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Repository creation date"
    )

    repository_updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last repository update"
    )

    # Hype scores (calculated from star velocity)
    average_hype: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Average daily star gain (all-time)"
    )

    weekly_hype: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Star gain in last 7 days"
    )

    monthly_hype: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Star gain in last 30 days"
    )

    # Tracking metadata
    tracking_start_date: Mapped[date] = mapped_column(
        nullable=False,
        comment="Date when tracking began"
    )

    last_tracked_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False,
        comment="Last successful tracking timestamp"
    )

    tracking_enabled: Mapped[bool] = mapped_column(
        default=True,
        server_default=text("true"),
        nullable=False,
        comment="Enable/disable tracking"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="github_metrics"
    )

    star_history: Mapped[list["GitHubStarSnapshot"]] = relationship(
        "GitHubStarSnapshot",
        back_populates="metrics",
        cascade="all, delete-orphan",
        order_by="GitHubStarSnapshot.snapshot_date.desc()"
    )

    __table_args__ = (
        Index("idx_github_metrics_weekly_hype", "weekly_hype", postgresql_ops={"weekly_hype": "DESC"}),
        Index("idx_github_metrics_monthly_hype", "monthly_hype", postgresql_ops={"monthly_hype": "DESC"}),
        Index("idx_github_metrics_stars", "current_stars", postgresql_ops={"current_stars": "DESC"}),
        Index("idx_github_metrics_owner", "repository_owner"),
    )

    def __repr__(self) -> str:
        return f"<GitHubMetrics({self.repository_name}: {self.current_stars} stars)>"


class GitHubStarSnapshot(Base):
    """Daily star count snapshots (TimescaleDB hypertable).

    Stores historical star counts for calculating velocity metrics.
    """

    __tablename__ = "github_star_snapshots"

    # Composite primary key (time-series)
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("github_metrics.paper_id", ondelete="CASCADE"),
        primary_key=True
    )

    snapshot_date: Mapped[date] = mapped_column(
        primary_key=True,
        comment="Date of snapshot (UTC)"
    )

    # Metrics at snapshot time
    star_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Star count at snapshot time"
    )

    fork_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Fork count at snapshot time"
    )

    watcher_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Watcher count at snapshot time"
    )

    # Calculated deltas
    stars_gained_since_yesterday: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Star delta from previous day"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )

    # Relationships
    metrics: Mapped["GitHubMetrics"] = relationship(
        "GitHubMetrics",
        back_populates="star_history"
    )

    __table_args__ = (
        Index("idx_star_snapshots_date", "snapshot_date", postgresql_ops={"snapshot_date": "DESC"}),
        Index("idx_star_snapshots_paper_date", "paper_id", "snapshot_date"),
    )

    def __repr__(self) -> str:
        return f"<StarSnapshot({self.paper_id}, {self.snapshot_date}: {self.star_count})>"
```

**TimescaleDB Setup**:
```sql
-- Convert to hypertable for efficient time-series queries
SELECT create_hypertable('github_star_snapshots', 'snapshot_date', chunk_time_interval => INTERVAL '7 days');

-- Compression policy (compress data older than 90 days)
ALTER TABLE github_star_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'paper_id'
);

SELECT add_compression_policy('github_star_snapshots', INTERVAL '90 days');

-- Retention policy (optional: keep last 2 years only)
-- SELECT add_retention_policy('github_star_snapshots', INTERVAL '2 years');
```

**Query Patterns**:
```python
# Get star velocity for last 30 days
recent_snapshots = (
    session.query(GitHubStarSnapshot)
    .filter(
        GitHubStarSnapshot.paper_id == paper_id,
        GitHubStarSnapshot.snapshot_date >= date.today() - timedelta(days=30)
    )
    .order_by(GitHubStarSnapshot.snapshot_date.desc())
    .all()
)

# Aggregate query: Papers with highest weekly hype
trending_papers = (
    session.query(Paper, GitHubMetrics)
    .join(GitHubMetrics)
    .filter(GitHubMetrics.tracking_enabled == True)
    .order_by(GitHubMetrics.weekly_hype.desc())
    .limit(100)
    .all()
)
```

---

### 5. PDFContent

Extracted content from paper PDFs including full text and tables.

**Table Name**: `pdf_contents`

```python
from sqlalchemy import ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PDFContent(Base):
    """Extracted content from paper PDFs.

    One-to-one relationship with Paper.
    Stores full text, tables, and references.
    """

    __tablename__ = "pdf_contents"

    # Primary key (also foreign key)
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Extracted text content
    full_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Complete extracted text from PDF"
    )

    # References section
    references_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw text from References/Bibliography section"
    )

    parsed_references: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of parsed citation strings"
    )

    # Table extraction
    table_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Number of tables extracted"
    )

    table_csv_paths: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of CSV file paths: ['paper.table00.csv', ...]"
    )

    # Extraction metadata
    extraction_method: Mapped[str] = mapped_column(
        String(50),
        default="pymupdf",
        nullable=False,
        comment="PDF parser used: 'pymupdf', 'pdfplumber'"
    )

    table_extraction_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Table extractor used: 'gmft', 'camelot'"
    )

    extraction_success: Mapped[bool] = mapped_column(
        default=True,
        server_default=text("true"),
        nullable=False,
        comment="Whether extraction succeeded"
    )

    extraction_errors: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of error messages if extraction failed"
    )

    # Parser versions
    pymupdf_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="PyMuPDF version used"
    )

    gmft_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="GMFT version used for table extraction"
    )

    # Timestamps
    extracted_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False,
        comment="When PDF was processed"
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="pdf_content"
    )

    __table_args__ = (
        Index(
            "idx_pdf_contents_fulltext_fts",
            text("to_tsvector('english', full_text)"),
            postgresql_using="gin",
        ),
        Index(
            "idx_pdf_contents_references_fts",
            text("to_tsvector('english', references_text)"),
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<PDFContent({self.paper_id}: {len(self.full_text)} chars, {self.table_count} tables)>"
```

**Validation Rules**:
1. Full text must not be empty
2. Table count must be >= 0
3. Extraction method must be valid: `['pymupdf', 'pdfplumber']`

---

### 6. LLMExtraction

AI-extracted metadata from paper content with verification workflow.

**Table Name**: `llm_extractions`

```python
from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class ExtractionType(enum.Enum):
    """Types of LLM extractions."""
    TASK = "task"
    METHOD = "method"
    DATASET = "dataset"
    METRIC = "metric"
    LIMITATION = "limitation"
    COMPARISON = "comparison"


class VerificationStatus(enum.Enum):
    """Verification workflow states."""
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    AUTO_ACCEPTED = "auto_accepted"  # Future: ML-based auto-verification


class LLMExtraction(Base):
    """AI-extracted metadata from paper content.

    Many-to-one relationship with Paper.
    Supports manual verification workflow.
    """

    __tablename__ = "llm_extractions"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Foreign key
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Extraction type
    extraction_type: Mapped[ExtractionType] = mapped_column(
        Enum(ExtractionType),
        nullable=False,
        index=True,
        comment="Type of metadata extracted"
    )

    # Extracted data
    primary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Primary extracted value"
    )

    secondary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Secondary extracted value"
    )

    tertiary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Tertiary extracted value"
    )

    all_values: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="All extracted values (for datasets/metrics)"
    )

    # LLM metadata
    llm_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="LLM provider: 'openai', 'llamacpp'"
    )

    llm_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Model name: 'gpt-4', 'Polaris-7B-preview'"
    )

    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Prompt template version for reproducibility"
    )

    raw_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw LLM response for debugging"
    )

    # Verification workflow
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING_REVIEW,
        server_default=text("'pending_review'"),
        nullable=False,
        index=True,
        comment="Manual verification state"
    )

    verified_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Username of verifier"
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Verification timestamp"
    )

    verification_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verifier notes or rejection reason"
    )

    # Timestamps
    extracted_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="llm_extractions"
    )

    __table_args__ = (
        Index("idx_llm_extractions_paper", "paper_id"),
        Index("idx_llm_extractions_type_status", "extraction_type", "verification_status"),
        Index("idx_llm_extractions_pending", "verification_status").where(
            text("verification_status = 'pending_review'")
        ),
    )

    def __repr__(self) -> str:
        return f"<LLMExtraction({self.extraction_type.value}, {self.verification_status.value})>"
```

**Validation Rules**:
1. Extraction type must be valid enum value
2. Verification status must be valid enum value
3. At least one value field must be non-null (`primary_value` or `all_values`)
4. If status is `verified` or `rejected`, `verified_by` and `verified_at` must be set

**State Transitions**:
```
pending_review -> verified (manual approval)
pending_review -> rejected (manual rejection)
pending_review -> auto_accepted (future: ML confidence threshold)
verified -> pending_review (re-review requested)
rejected -> pending_review (re-extraction requested)
```

---

## Database Migration Script

Alembic migration to add legacy fields to existing schema:

```python
"""Add SOTAPapers legacy fields

Revision ID: add_legacy_fields
Revises: previous_migration
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_legacy_fields'
down_revision = 'previous_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add legacy fields to papers table
    op.add_column('papers', sa.Column('legacy_id', sa.String(100), nullable=True, comment='SHA256 hash of normalized(title + year)'))
    op.add_column('papers', sa.Column('affiliations', postgresql.JSONB(), nullable=True, comment='Author affiliations'))
    op.add_column('papers', sa.Column('affiliations_country', postgresql.JSONB(), nullable=True, comment='Countries from affiliations'))
    op.add_column('papers', sa.Column('year', sa.Integer(), nullable=True, comment='Publication year'))
    op.add_column('papers', sa.Column('pages', postgresql.JSONB(), nullable=True, comment='Page range'))
    op.add_column('papers', sa.Column('paper_type', sa.String(50), nullable=True, comment='Paper type'))
    op.add_column('papers', sa.Column('session_type', sa.String(100), nullable=True, comment='Conference session'))
    op.add_column('papers', sa.Column('accept_status', sa.String(50), nullable=True, comment='Acceptance status'))
    op.add_column('papers', sa.Column('note', sa.Text(), nullable=True, comment='Additional notes'))
    op.add_column('papers', sa.Column('bibtex', sa.Text(), nullable=True, comment='BibTeX entry'))
    op.add_column('papers', sa.Column('primary_task', sa.String(200), nullable=True, comment='Primary research task'))
    op.add_column('papers', sa.Column('secondary_task', sa.String(200), nullable=True, comment='Secondary task'))
    op.add_column('papers', sa.Column('tertiary_task', sa.String(200), nullable=True, comment='Tertiary task'))
    op.add_column('papers', sa.Column('primary_method', sa.String(200), nullable=True, comment='Primary method'))
    op.add_column('papers', sa.Column('secondary_method', sa.String(200), nullable=True, comment='Secondary method'))
    op.add_column('papers', sa.Column('tertiary_method', sa.String(200), nullable=True, comment='Tertiary method'))
    op.add_column('papers', sa.Column('datasets_used', postgresql.JSONB(), nullable=True, comment='Datasets mentioned'))
    op.add_column('papers', sa.Column('metrics_used', postgresql.JSONB(), nullable=True, comment='Evaluation metrics'))
    op.add_column('papers', sa.Column('comparisons', postgresql.JSONB(), nullable=True, comment='Comparison results'))
    op.add_column('papers', sa.Column('limitations', sa.Text(), nullable=True, comment='Paper limitations'))
    op.add_column('papers', sa.Column('youtube_url', sa.String(500), nullable=True, comment='YouTube video URL'))
    op.add_column('papers', sa.Column('project_page_url', sa.String(500), nullable=True, comment='Project page URL'))
    op.add_column('papers', sa.Column('github_star_tracking_start_date', sa.Date(), nullable=True, comment='Tracking start date'))
    op.add_column('papers', sa.Column('github_star_tracking_latest_footprint', postgresql.JSONB(), nullable=True, comment='Latest snapshot'))

    # Create indexes
    op.create_index('idx_papers_legacy_id', 'papers', ['legacy_id'], unique=True)
    op.create_index('idx_papers_year_desc', 'papers', ['year'], postgresql_ops={'year': 'DESC'})
    op.create_index('idx_papers_affiliations_gin', 'papers', ['affiliations'], postgresql_using='gin')
    op.create_index('idx_papers_datasets_gin', 'papers', ['datasets_used'], postgresql_using='gin')
    op.create_index('idx_papers_metrics_gin', 'papers', ['metrics_used'], postgresql_using='gin')
    op.create_index('idx_papers_task_year', 'papers', ['primary_task', 'year'])
    op.create_index('idx_papers_abstract_fts', 'papers', [sa.text("to_tsvector('english', abstract)")], postgresql_using='gin')

    # Create new tables
    # Authors
    op.create_table(
        'authors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False, comment='Full author name'),
        sa.Column('affiliations', postgresql.JSONB(), nullable=True),
        sa.Column('countries', postgresql.JSONB(), nullable=True),
        sa.Column('paper_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_authors_name', 'authors', ['name'], unique=True)
    op.create_index('idx_authors_name_fts', 'authors', [sa.text("to_tsvector('english', name)")], postgresql_using='gin')
    op.create_index('idx_authors_affiliations_gin', 'authors', ['affiliations'], postgresql_using='gin')

    # Paper-Author junction
    op.create_table(
        'paper_authors',
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('affiliation_snapshot', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id', 'author_id')
    )
    op.create_index('idx_paper_authors_paper', 'paper_authors', ['paper_id'])
    op.create_index('idx_paper_authors_author', 'paper_authors', ['author_id'])

    # Citations
    op.create_table(
        'paper_references',
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_text', sa.Text(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('match_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reference_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id', 'reference_id'),
        sa.CheckConstraint('paper_id != reference_id', name='no_self_citation'),
        sa.CheckConstraint('match_score >= 0 AND match_score <= 100 OR match_score IS NULL', name='match_score_valid_range')
    )
    op.create_index('idx_citations_paper', 'paper_references', ['paper_id'])
    op.create_index('idx_citations_reference', 'paper_references', ['reference_id'])
    op.create_index('idx_citations_match_score', 'paper_references', ['match_score'], postgresql_ops={'match_score': 'DESC'})

    # GitHub Metrics
    op.create_table(
        'github_metrics',
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_url', sa.String(500), nullable=False),
        sa.Column('repository_owner', sa.String(100), nullable=False),
        sa.Column('repository_name', sa.String(200), nullable=False),
        sa.Column('current_stars', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('current_forks', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('current_watchers', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('primary_language', sa.String(50), nullable=True),
        sa.Column('repository_description', sa.Text(), nullable=True),
        sa.Column('repository_created_at', sa.DateTime(), nullable=True),
        sa.Column('repository_updated_at', sa.DateTime(), nullable=True),
        sa.Column('average_hype', sa.Float(), nullable=True),
        sa.Column('weekly_hype', sa.Float(), nullable=True),
        sa.Column('monthly_hype', sa.Float(), nullable=True),
        sa.Column('tracking_start_date', sa.Date(), nullable=False),
        sa.Column('last_tracked_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('tracking_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id')
    )
    op.create_index('idx_github_metrics_url', 'github_metrics', ['repository_url'], unique=True)
    op.create_index('idx_github_metrics_owner', 'github_metrics', ['repository_owner'])
    op.create_index('idx_github_metrics_stars', 'github_metrics', ['current_stars'], postgresql_ops={'current_stars': 'DESC'})
    op.create_index('idx_github_metrics_weekly_hype', 'github_metrics', ['weekly_hype'], postgresql_ops={'weekly_hype': 'DESC'})
    op.create_index('idx_github_metrics_monthly_hype', 'github_metrics', ['monthly_hype'], postgresql_ops={'monthly_hype': 'DESC'})

    # GitHub Star Snapshots (TimescaleDB)
    op.create_table(
        'github_star_snapshots',
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('star_count', sa.Integer(), nullable=False),
        sa.Column('fork_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('watcher_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('stars_gained_since_yesterday', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['github_metrics.paper_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id', 'snapshot_date')
    )
    op.create_index('idx_star_snapshots_date', 'github_star_snapshots', ['snapshot_date'], postgresql_ops={'snapshot_date': 'DESC'})
    op.create_index('idx_star_snapshots_paper_date', 'github_star_snapshots', ['paper_id', 'snapshot_date'])

    # Convert to TimescaleDB hypertable
    op.execute("SELECT create_hypertable('github_star_snapshots', 'snapshot_date', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);")

    # PDF Content
    op.create_table(
        'pdf_contents',
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('references_text', sa.Text(), nullable=True),
        sa.Column('parsed_references', postgresql.JSONB(), nullable=True),
        sa.Column('table_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('table_csv_paths', postgresql.JSONB(), nullable=True),
        sa.Column('extraction_method', sa.String(50), server_default=sa.text("'pymupdf'"), nullable=False),
        sa.Column('table_extraction_method', sa.String(50), nullable=True),
        sa.Column('extraction_success', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('extraction_errors', postgresql.JSONB(), nullable=True),
        sa.Column('pymupdf_version', sa.String(20), nullable=True),
        sa.Column('gmft_version', sa.String(20), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id')
    )
    op.create_index('idx_pdf_contents_fulltext_fts', 'pdf_contents', [sa.text("to_tsvector('english', full_text)")], postgresql_using='gin')
    op.create_index('idx_pdf_contents_references_fts', 'pdf_contents', [sa.text("to_tsvector('english', references_text)")], postgresql_using='gin')

    # LLM Extractions
    op.create_table(
        'llm_extractions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extraction_type', sa.Enum('TASK', 'METHOD', 'DATASET', 'METRIC', 'LIMITATION', 'COMPARISON', name='extractiontype'), nullable=False),
        sa.Column('primary_value', sa.Text(), nullable=True),
        sa.Column('secondary_value', sa.Text(), nullable=True),
        sa.Column('tertiary_value', sa.Text(), nullable=True),
        sa.Column('all_values', postgresql.JSONB(), nullable=True),
        sa.Column('llm_provider', sa.String(50), nullable=False),
        sa.Column('llm_model', sa.String(100), nullable=False),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.Enum('PENDING_REVIEW', 'VERIFIED', 'REJECTED', 'AUTO_ACCEPTED', name='verificationstatus'), server_default=sa.text("'PENDING_REVIEW'"), nullable=False),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_llm_extractions_paper', 'llm_extractions', ['paper_id'])
    op.create_index('idx_llm_extractions_type_status', 'llm_extractions', ['extraction_type', 'verification_status'])

    # Update constraint on papers to allow legacy_id as ID
    op.drop_constraint('at_least_one_id', 'papers', type_='check')
    op.create_check_constraint(
        'at_least_one_id',
        'papers',
        'arxiv_id IS NOT NULL OR doi IS NOT NULL OR legacy_id IS NOT NULL'
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table('llm_extractions')
    op.drop_table('pdf_contents')
    op.drop_table('github_star_snapshots')
    op.drop_table('github_metrics')
    op.drop_table('paper_references')
    op.drop_table('paper_authors')
    op.drop_table('authors')

    # Drop new columns from papers
    op.drop_column('papers', 'github_star_tracking_latest_footprint')
    op.drop_column('papers', 'github_star_tracking_start_date')
    op.drop_column('papers', 'project_page_url')
    op.drop_column('papers', 'youtube_url')
    op.drop_column('papers', 'limitations')
    op.drop_column('papers', 'comparisons')
    op.drop_column('papers', 'metrics_used')
    op.drop_column('papers', 'datasets_used')
    op.drop_column('papers', 'tertiary_method')
    op.drop_column('papers', 'secondary_method')
    op.drop_column('papers', 'primary_method')
    op.drop_column('papers', 'tertiary_task')
    op.drop_column('papers', 'secondary_task')
    op.drop_column('papers', 'primary_task')
    op.drop_column('papers', 'bibtex')
    op.drop_column('papers', 'note')
    op.drop_column('papers', 'accept_status')
    op.drop_column('papers', 'session_type')
    op.drop_column('papers', 'paper_type')
    op.drop_column('papers', 'pages')
    op.drop_column('papers', 'year')
    op.drop_column('papers', 'affiliations_country')
    op.drop_column('papers', 'affiliations')
    op.drop_column('papers', 'legacy_id')

    # Restore original constraint
    op.drop_constraint('at_least_one_id', 'papers', type_='check')
    op.create_check_constraint(
        'at_least_one_id',
        'papers',
        'arxiv_id IS NOT NULL OR doi IS NOT NULL'
    )
```

---

## Summary

This data model extends HypePaper with comprehensive paper metadata from SOTAPapers legacy:

1. **Paper**: Extended with 22 new fields (37 total legacy fields) for AI extractions, conference metadata, and tracking
2. **Author**: Many-to-many with papers, affiliation tracking
3. **PaperReference**: Bidirectional citations with fuzzy matching metadata
4. **GitHubMetrics**: Time-series star tracking with TimescaleDB hypertables
5. **PDFContent**: Full text and table extraction results
6. **LLMExtraction**: AI metadata with manual verification workflow

All models support PostgreSQL-specific optimizations (JSONB, GIN indexes, full-text search) and async SQLAlchemy operations.
