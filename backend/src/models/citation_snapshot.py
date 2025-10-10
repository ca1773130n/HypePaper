"""Citation snapshot model for tracking citation counts over time."""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, String, Integer, text, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


class CitationSnapshot(Base):
    """Historical citation count snapshot.

    Tracks citation counts over time for papers to show citation growth trends.
    """

    __tablename__ = "citation_snapshots"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Foreign key to paper
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Citation count at this snapshot
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Date of snapshot
    snapshot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        server_default=text("CURRENT_DATE"),
    )

    # Source of citation data
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="google_scholar",
        server_default=text("'google_scholar'"),
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False,
    )

    # Unique constraint: one snapshot per paper per day per source
    __table_args__ = (
        UniqueConstraint(
            'paper_id',
            'snapshot_date',
            'source',
            name='unique_paper_citation_snapshot'
        ),
    )

    # Relationship to paper
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="citation_snapshots",
        foreign_keys=[paper_id],
    )
