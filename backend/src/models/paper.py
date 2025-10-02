"""Paper model for research papers.

Represents papers from arXiv or conference venues with metadata.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Paper(Base):
    """Research paper entity.

    Fields:
    - id: Internal UUID identifier
    - arxiv_id: arXiv identifier (e.g., "2301.12345")
    - doi: Digital Object Identifier
    - title: Paper title (10-500 chars)
    - authors: List of author names (at least 1)
    - abstract: Paper abstract text
    - published_date: Publication date (cannot be future)
    - venue: Conference/journal name (optional)
    - github_url: Link to GitHub repository (optional)
    - arxiv_url: Link to arXiv page (optional)
    - pdf_url: Link to PDF (optional)
    - created_at: Record creation timestamp
    - updated_at: Last update timestamp

    Constraints:
    - At least one of arxiv_id or doi must be present
    - Title length: 10-500 characters
    - Published date cannot be in the future
    """

    __tablename__ = "papers"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Canonical identifiers (at least one required)
    arxiv_id: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    doi: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )

    # Metadata
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

    # Relationships
    metric_snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        "MetricSnapshot", back_populates="paper", cascade="all, delete-orphan"
    )
    topic_matches: Mapped[list["PaperTopicMatch"]] = relationship(
        "PaperTopicMatch", back_populates="paper", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "arxiv_id IS NOT NULL OR doi IS NOT NULL",
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
        # Index for published_date (descending for recent papers first)
        Index("idx_papers_published_date", "published_date", postgresql_ops={"published_date": "DESC"}),
        # Full-text search index on title
        Index(
            "idx_papers_title_fts",
            text("to_tsvector('english', title)"),
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        identifier = self.arxiv_id or self.doi or str(self.id)
        return f"<Paper({identifier}): {self.title[:50]}...>"
