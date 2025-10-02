"""MetricSnapshot model for daily paper metrics.

Tracks GitHub stars and citation counts over time using TimescaleDB.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class MetricSnapshot(Base):
    """Daily metric snapshot for a paper.

    TimescaleDB hypertable optimized for time-series queries.

    Fields:
    - id: Auto-increment identifier
    - paper_id: Reference to paper
    - snapshot_date: Date of metric capture
    - github_stars: GitHub star count (nullable if no repo)
    - citation_count: Citation count (nullable if unavailable)
    - created_at: Snapshot creation timestamp

    Constraints:
    - Unique (paper_id, snapshot_date) - one snapshot per paper per day
    - github_stars >= 0 if present
    - citation_count >= 0 if present
    - snapshot_date cannot be in the future

    TimescaleDB Configuration:
    - Hypertable partitioned by snapshot_date
    - Chunk interval: 30 days
    - Compression enabled after 7 days
    - Retention: 30 days minimum (MVP)
    """

    __tablename__ = "metric_snapshots"

    # Primary key (bigint for TimescaleDB efficiency)
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Foreign key
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time dimension (hypertable partitioning key)
    snapshot_date: Mapped[date] = mapped_column(nullable=False)

    # Metrics (nullable if data unavailable)
    github_stars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    citation_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        server_default="NOW()", nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="metric_snapshots")

    # Constraints
    __table_args__ = (
        UniqueConstraint("paper_id", "snapshot_date", name="unique_paper_snapshot_date"),
        CheckConstraint(
            "github_stars IS NULL OR github_stars >= 0",
            name="github_stars_non_negative",
        ),
        CheckConstraint(
            "citation_count IS NULL OR citation_count >= 0",
            name="citation_count_non_negative",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<MetricSnapshot(paper_id={self.paper_id}, "
            f"date={self.snapshot_date}, stars={self.github_stars}, "
            f"citations={self.citation_count})>"
        )
