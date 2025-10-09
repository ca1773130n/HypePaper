"""GitHub metrics models for repository tracking.

Time-series tracking of GitHub repository metrics with TimescaleDB.
One-to-one relationship with Paper for current metrics.
One-to-many for historical star snapshots.
"""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


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
