"""Hype score calculation service.

Calculates hype scores for papers based on GitHub stars, citations, and votes
using the formula from the plan:

hype_score = (
    0.40 * log_component(github_stars, base=10) +
    0.30 * log_component(citations, base=10) +
    0.20 * log_component(votes, base=2) +
    0.10 * recency_component(days_since_publication)
)

Where log_component uses logarithmic scaling to prevent domination by outliers.
"""
import math
from datetime import date, datetime
from typing import Optional


def calculate_log_component(value: int, base: float = 10) -> float:
    """Calculate logarithmic component for a metric value.

    Uses log(value + 1) to handle zero values and provide diminishing returns.

    Args:
        value: Metric value (stars, citations, votes)
        base: Logarithm base (default 10 for stars/citations, 2 for votes)

    Returns:
        float: Normalized logarithmic score [0, 1] based on practical max
    """
    if value < 0:
        return 0.0

    # Practical maximums for normalization
    # - GitHub stars: 100k (log10(100001) ≈ 5.0)
    # - Citations: 10k (log10(10001) ≈ 4.0)
    # - Votes: 1k (log2(1001) ≈ 10.0)
    max_log_values = {
        10: 5.0,  # base 10 → max ~5.0 for 100k
        2: 10.0,   # base 2 → max ~10.0 for 1k
    }

    max_log = max_log_values.get(base, 5.0)
    log_value = math.log(value + 1, base)

    # Normalize to [0, 1]
    return min(log_value / max_log, 1.0)


def calculate_vote_component(vote_count: int) -> float:
    """Calculate vote component using logarithmic scaling (base 2).

    Negative votes clamped to 0.

    Args:
        vote_count: Net vote count (upvotes - downvotes)

    Returns:
        float: Vote component score [0, 1]
    """
    if vote_count <= 0:
        return 0.0

    return calculate_log_component(vote_count, base=2)


def calculate_recency_component(published_date: date) -> float:
    """Calculate recency component using exponential decay.

    Papers lose half their recency score every 365 days.

    Args:
        published_date: Paper publication date

    Returns:
        float: Recency score [0, 1]
    """
    today = date.today()
    days_since_publication = (today - published_date).days

    # Exponential decay: score = 2^(-days / half_life)
    # Half-life = 365 days (1 year)
    half_life = 365.0
    recency_score = math.pow(2, -days_since_publication / half_life)

    return max(0.0, min(recency_score, 1.0))


def calculate_hype_score(
    github_stars: Optional[int] = None,
    citation_count: Optional[int] = None,
    vote_count: Optional[int] = None,
    published_date: Optional[date] = None
) -> float:
    """Calculate hype score from all available metrics.

    Formula:
    hype_score = (
        0.40 * log_component(github_stars, base=10) +
        0.30 * log_component(citations, base=10) +
        0.20 * log_component(votes, base=2) +
        0.10 * recency_component(days_since_publication)
    )

    Missing metrics default to 0.0 for their component.

    Args:
        github_stars: GitHub star count (optional)
        citation_count: Citation count (optional)
        vote_count: Net vote count (optional)
        published_date: Publication date (optional)

    Returns:
        float: Hype score [0, 1] (typically much lower in practice)
    """
    # GitHub component (40%)
    github_component = 0.0
    if github_stars is not None:
        github_component = 0.40 * calculate_log_component(github_stars, base=10)

    # Citation component (30%)
    citation_component = 0.0
    if citation_count is not None:
        citation_component = 0.30 * calculate_log_component(citation_count, base=10)

    # Vote component (20%)
    vote_component_value = 0.0
    if vote_count is not None:
        vote_component_value = 0.20 * calculate_vote_component(vote_count)

    # Recency component (10%)
    recency_component_value = 0.0
    if published_date is not None:
        recency_component_value = 0.10 * calculate_recency_component(published_date)

    hype_score = (
        github_component +
        citation_component +
        vote_component_value +
        recency_component_value
    )

    return max(0.0, hype_score)


class HypeScoreService:
    """Service for calculating and updating paper hype scores."""

    @staticmethod
    def calculate_for_paper(paper) -> float:
        """Calculate hype score for a Paper model instance.

        Args:
            paper: Paper model instance

        Returns:
            float: Calculated hype score
        """
        github_stars = None
        if paper.github_metrics:
            github_stars = paper.github_metrics.current_stars

        return calculate_hype_score(
            github_stars=github_stars,
            citation_count=paper.citation_count,
            vote_count=paper.vote_count,
            published_date=paper.published_date
        )

    @staticmethod
    def calculate_for_snapshot(
        github_stars: Optional[int],
        citation_count: Optional[int],
        vote_count: Optional[int],
        published_date: date
    ) -> float:
        """Calculate hype score for a MetricSnapshot.

        Args:
            github_stars: Star count at snapshot time
            citation_count: Citation count at snapshot time
            vote_count: Vote count at snapshot time
            published_date: Paper publication date (for recency)

        Returns:
            float: Calculated hype score
        """
        return calculate_hype_score(
            github_stars=github_stars,
            citation_count=citation_count,
            vote_count=vote_count,
            published_date=published_date
        )
