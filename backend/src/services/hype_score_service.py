"""HypeScoreService for calculating trending scores.

Implements the hype score formula from research.md:
hype_score = (
    0.4 * star_growth_rate_7d +
    0.3 * citation_growth_rate_30d +
    0.2 * absolute_stars_normalized +
    0.1 * recency_bonus
) * 100
"""
import math
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paper
from .metric_service import MetricService


class HypeScoreService:
    """Service for calculating hype scores and growth rates."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.metric_service = MetricService(session)

    async def calculate_hype_score(
        self,
        paper: Paper,
        topic_max_stars: int = 10000,
    ) -> dict:
        """Calculate hype score and components for a paper.

        Args:
            paper: Paper entity
            topic_max_stars: Maximum stars in topic for normalization

        Returns:
            Dictionary with hype_score and all components
        """
        today = date.today()

        # Get metric snapshots
        latest_metric = await self.metric_service.get_latest_metric(paper.id)
        metric_7d_ago = await self.metric_service.get_metric_at_date(
            paper.id, today - timedelta(days=7)
        )
        metric_30d_ago = await self.metric_service.get_metric_at_date(
            paper.id, today - timedelta(days=30)
        )

        # Calculate star growth rate (7-day)
        star_growth_7d = self._calculate_growth_rate(
            current_metric=latest_metric,
            past_metric=metric_7d_ago,
            field="github_stars",
        )

        # Calculate citation growth rate (30-day)
        citation_growth_30d = self._calculate_growth_rate(
            current_metric=latest_metric,
            past_metric=metric_30d_ago,
            field="citation_count",
        )

        # Normalize absolute stars
        current_stars = latest_metric.github_stars if latest_metric else 0
        absolute_stars_norm = self._normalize_stars(
            current_stars, topic_max_stars
        )

        # Calculate recency bonus
        recency_bonus = self._calculate_recency_bonus(paper.published_date)

        # Calculate final hype score
        hype_score = (
            0.4 * star_growth_7d
            + 0.3 * citation_growth_30d
            + 0.2 * absolute_stars_norm
            + 0.1 * recency_bonus
        ) * 100

        # Clamp to 0-100
        hype_score = max(0.0, min(100.0, hype_score))

        # Determine trend label
        trend_label = self._get_trend_label(star_growth_7d)

        return {
            "hype_score": round(hype_score, 2),
            "star_growth_7d": round(star_growth_7d, 4),
            "citation_growth_30d": round(citation_growth_30d, 4),
            "absolute_stars_norm": round(absolute_stars_norm, 4),
            "recency_bonus": round(recency_bonus, 4),
            "trend_label": trend_label,
            "current_stars": current_stars,
        }

    def _calculate_growth_rate(
        self,
        current_metric,
        past_metric,
        field: str,
    ) -> float:
        """Calculate growth rate for a metric field.

        Args:
            current_metric: Latest metric snapshot
            past_metric: Past metric snapshot
            field: Field name ("github_stars" or "citation_count")

        Returns:
            Growth rate (0.0-1.0+)
        """
        if not current_metric or not past_metric:
            return 0.0

        current_value = getattr(current_metric, field)
        past_value = getattr(past_metric, field)

        if current_value is None or past_value is None:
            return 0.0

        # Prevent division by zero
        if past_value == 0:
            return 1.0 if current_value > 0 else 0.0

        growth_rate = (current_value - past_value) / past_value
        return max(0.0, growth_rate)  # Clamp negative growth to 0

    def _normalize_stars(
        self, current_stars: Optional[int], max_stars: int
    ) -> float:
        """Normalize star count using logarithmic scale.

        Args:
            current_stars: Current GitHub star count
            max_stars: Maximum stars in topic

        Returns:
            Normalized value (0.0-1.0)
        """
        if not current_stars or current_stars <= 0:
            return 0.0

        if max_stars <= 1:
            return 0.0

        # Logarithmic normalization
        normalized = math.log10(current_stars + 1) / math.log10(max_stars + 1)
        return max(0.0, min(1.0, normalized))

    def _calculate_recency_bonus(self, published_date: date) -> float:
        """Calculate recency bonus based on publication date.

        Papers published within 30 days get full bonus (1.0).
        Bonus decays linearly over next 30 days to 0.0.

        Args:
            published_date: Paper publication date

        Returns:
            Recency bonus (0.0-1.0)
        """
        days_since_publish = (date.today() - published_date).days

        if days_since_publish < 0:
            # Future date (should not happen due to constraints)
            return 0.0
        elif days_since_publish <= 30:
            return 1.0
        elif days_since_publish <= 60:
            # Linear decay from 1.0 to 0.0 over 30 days
            return max(0.0, 1.0 - (days_since_publish - 30) / 30)
        else:
            return 0.0

    def _get_trend_label(self, star_growth_7d: float) -> str:
        """Determine trend label from growth rate.

        Args:
            star_growth_7d: 7-day star growth rate

        Returns:
            "rising", "stable", or "declining"
        """
        if star_growth_7d > 0.1:  # >10% growth
            return "rising"
        elif star_growth_7d < -0.05:  # <-5% decline
            return "declining"
        else:
            return "stable"
