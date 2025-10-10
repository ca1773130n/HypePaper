"""Paper reference (citation) model.

Bidirectional citation relationships between papers with original reference text preservation.
Represents: Paper A cites Paper B (paper_id -> reference_id)
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


class PaperReference(Base):
    """Citation relationship between papers (bidirectional).

    Represents: Paper A cites Paper B
    - source_paper_id: Source paper (A)
    - target_paper_id: Cited paper (B)
    """

    __tablename__ = "paper_references"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Primary key"
    )

    # Foreign keys
    source_paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Paper containing the citation"
    )

    target_paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Paper being cited"
    )

    # Target paper metadata (denormalized for quick lookups)
    target_title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Title of cited paper"
    )

    target_authors: Mapped[Optional[list]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Authors of cited paper"
    )

    target_year: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Publication year of cited paper"
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
    source_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[source_paper_id],
        back_populates="citations_out"
    )

    target_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[target_paper_id],
        back_populates="citations_in"
    )

    __table_args__ = (
        CheckConstraint(
            "source_paper_id != target_paper_id",
            name="no_self_citation"
        ),
        CheckConstraint(
            "match_score >= 0 AND match_score <= 100 OR match_score IS NULL",
            name="match_score_valid_range"
        ),
        Index("idx_citations_source", "source_paper_id"),
        Index("idx_citations_target", "target_paper_id"),
        Index("idx_citations_match_score", "match_score", postgresql_ops={"match_score": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Citation({self.source_paper_id} -> {self.target_paper_id}, score={self.match_score})>"
