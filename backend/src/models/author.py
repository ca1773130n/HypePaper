"""Author models for paper authorship.

Represents paper authors with affiliation tracking across multiple papers.
Many-to-many relationship with papers via paper_authors junction table.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


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
        # unique=True removed for Feature 003 - allow name+affiliation disambiguation
        index=True,
        comment="Full author name (normalized)"
    )

    # Affiliations across all papers
    affiliations: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of institutions: ['MIT', 'Stanford', ...]"
    )

    # Statistics
    paper_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Total papers authored"
    )

    # NEW FIELDS (Feature 003)
    total_citation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Sum of citations from all author's papers"
    )

    latest_paper_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to most recent paper"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Author email address"
    )

    website_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Personal or lab website URL"
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

    latest_paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
        foreign_keys=[latest_paper_id],
        uselist=False
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

    @property
    def primary_affiliation(self) -> Optional[str]:
        """Get most recent affiliation."""
        return self.affiliations[0] if self.affiliations else None

    @property
    def avg_citations_per_paper(self) -> float:
        """Average citations per paper."""
        return self.total_citation_count / self.paper_count if self.paper_count > 0 else 0.0

    def __repr__(self) -> str:
        return f"<Author({self.name}): {self.paper_count} papers, {self.total_citation_count} citations>"


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
