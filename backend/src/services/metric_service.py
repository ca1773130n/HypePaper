"""MetricService for managing metric snapshots."""
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MetricSnapshot


class MetricService:
    """Service for metric snapshot operations.

    Handles querying and creating metric snapshots for papers.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def get_metrics(
        self,
        paper_id: UUID,
        days: int = 30,
    ) -> list[MetricSnapshot]:
        """Get metric snapshots for a paper.

        Args:
            paper_id: Paper UUID
            days: Number of days of history (default 30)

        Returns:
            List of metric snapshots ordered by date (oldest first)
        """
        cutoff_date = date.today() - timedelta(days=days)

        query = (
            select(MetricSnapshot)
            .where(
                and_(
                    MetricSnapshot.paper_id == paper_id,
                    MetricSnapshot.snapshot_date >= cutoff_date,
                )
            )
            .order_by(MetricSnapshot.snapshot_date.asc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_metric(
        self, paper_id: UUID
    ) -> Optional[MetricSnapshot]:
        """Get most recent metric snapshot for a paper.

        Args:
            paper_id: Paper UUID

        Returns:
            Latest metric snapshot or None
        """
        query = (
            select(MetricSnapshot)
            .where(MetricSnapshot.paper_id == paper_id)
            .order_by(MetricSnapshot.snapshot_date.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_metric_at_date(
        self, paper_id: UUID, snapshot_date: date
    ) -> Optional[MetricSnapshot]:
        """Get metric snapshot for a specific date.

        Args:
            paper_id: Paper UUID
            snapshot_date: Date to query

        Returns:
            Metric snapshot if exists, None otherwise
        """
        query = select(MetricSnapshot).where(
            and_(
                MetricSnapshot.paper_id == paper_id,
                MetricSnapshot.snapshot_date == snapshot_date,
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_metric_snapshot(
        self,
        paper_id: UUID,
        snapshot_date: date,
        github_stars: Optional[int] = None,
        citation_count: Optional[int] = None,
    ) -> MetricSnapshot:
        """Create a new metric snapshot.

        Args:
            paper_id: Paper UUID
            snapshot_date: Date of snapshot
            github_stars: GitHub star count (optional)
            citation_count: Citation count (optional)

        Returns:
            Created metric snapshot
        """
        metric = MetricSnapshot(
            paper_id=paper_id,
            snapshot_date=snapshot_date,
            github_stars=github_stars,
            citation_count=citation_count,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_metric_range(
        self,
        paper_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[MetricSnapshot]:
        """Get metrics for a date range.

        Args:
            paper_id: Paper UUID
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)

        Returns:
            List of metric snapshots in range
        """
        query = (
            select(MetricSnapshot)
            .where(
                and_(
                    MetricSnapshot.paper_id == paper_id,
                    MetricSnapshot.snapshot_date >= start_date,
                    MetricSnapshot.snapshot_date <= end_date,
                )
            )
            .order_by(MetricSnapshot.snapshot_date.asc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
