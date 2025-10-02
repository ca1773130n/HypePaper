"""
Unit tests for hype score calculation logic.

Tests the hype score algorithm without requiring database access.
Formula: 40% star growth + 30% citation growth + 20% absolute metrics + 10% recency
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


class MockMetricSnapshot:
    """Mock metric snapshot for testing."""
    def __init__(self, stars: int, citations: int, snapshot_date: date):
        self.github_stars = stars
        self.citation_count = citations
        self.snapshot_date = snapshot_date


def calculate_hype_score(
    current_stars: int,
    current_citations: int,
    old_stars: int,
    old_citations: int,
    paper_age_days: int,
    max_stars: int = 10000,
    max_citations: int = 1000
) -> float:
    """
    Calculate hype score based on the formula from specs.

    Formula weights:
    - 40% star growth rate
    - 30% citation growth rate
    - 20% absolute metrics (normalized)
    - 10% recency bonus (newer papers get boost)
    """
    # Growth rates (avoid division by zero)
    star_growth = ((current_stars - old_stars) / max(old_stars, 1)) if old_stars > 0 else 0
    citation_growth = ((current_citations - old_citations) / max(old_citations, 1)) if old_citations > 0 else 0

    # Normalize absolute metrics
    normalized_stars = min(current_stars / max_stars, 1.0)
    normalized_citations = min(current_citations / max_citations, 1.0)
    absolute_score = (normalized_stars + normalized_citations) / 2

    # Recency bonus (papers < 30 days get full bonus, decays linearly to 0 at 365 days)
    recency_bonus = max(0, 1 - (paper_age_days / 365))

    # Weighted sum
    hype_score = (
        0.4 * star_growth +
        0.3 * citation_growth +
        0.2 * absolute_score +
        0.1 * recency_bonus
    )

    # Scale to 0-10
    return round(min(max(hype_score * 10, 0), 10), 2)


class TestHypeScoreCalculation:
    """Test suite for hype score calculation logic."""

    def test_viral_paper_high_growth(self):
        """Test paper with explosive growth gets high hype score."""
        # Paper went from 100 to 1000 stars, 10 to 100 citations in 30 days
        score = calculate_hype_score(
            current_stars=1000,
            current_citations=100,
            old_stars=100,
            old_citations=10,
            paper_age_days=30
        )

        # Should have high score due to 9x star growth and 9x citation growth
        assert score >= 7.0, f"Expected high hype score for viral paper, got {score}"

    def test_stable_paper_low_growth(self):
        """Test established paper with minimal growth gets lower score."""
        # Paper has high absolute metrics but minimal recent growth
        score = calculate_hype_score(
            current_stars=5000,
            current_citations=500,
            old_stars=4900,
            old_citations=490,
            paper_age_days=365
        )

        # Lower score due to minimal growth and no recency bonus
        assert score < 5.0, f"Expected lower score for stable paper, got {score}"

    def test_new_paper_recency_bonus(self):
        """Test that new papers get recency bonus."""
        # Same growth, different ages
        new_paper_score = calculate_hype_score(
            current_stars=200,
            current_citations=20,
            old_stars=100,
            old_citations=10,
            paper_age_days=7  # 1 week old
        )

        old_paper_score = calculate_hype_score(
            current_stars=200,
            current_citations=20,
            old_stars=100,
            old_citations=10,
            paper_age_days=365  # 1 year old
        )

        assert new_paper_score > old_paper_score, \
            f"New paper ({new_paper_score}) should score higher than old paper ({old_paper_score})"

    def test_zero_initial_metrics(self):
        """Test handling of papers with no initial metrics."""
        # New paper just added, no previous metrics
        score = calculate_hype_score(
            current_stars=50,
            current_citations=5,
            old_stars=0,
            old_citations=0,
            paper_age_days=1
        )

        # Should not crash and should give some score based on absolute + recency
        assert 0 <= score <= 10, f"Score {score} out of valid range [0, 10]"
        assert score > 0, "Paper with metrics should have non-zero score"

    def test_no_growth_zero_score(self):
        """Test that paper with no growth and no recency gets minimal score."""
        score = calculate_hype_score(
            current_stars=100,
            current_citations=10,
            old_stars=100,
            old_citations=10,
            paper_age_days=365
        )

        # Should have very low score (only from absolute metrics)
        assert score < 1.0, f"Expected minimal score for no growth, got {score}"

    def test_citation_growth_weighted_properly(self):
        """Test that citation growth contributes 30% to score."""
        # Paper with only citation growth (3x growth)
        score_citations = calculate_hype_score(
            current_stars=100,
            current_citations=30,  # 3x growth
            old_stars=100,
            old_citations=10,
            paper_age_days=180,
            max_stars=1000,
            max_citations=1000
        )

        # Paper with only star growth (3x growth)
        score_stars = calculate_hype_score(
            current_stars=300,  # 3x growth
            current_citations=10,
            old_stars=100,
            old_citations=10,
            paper_age_days=180,
            max_stars=1000,
            max_citations=1000
        )

        # Star growth (40%) should contribute more than citation growth (30%)
        assert score_stars > score_citations, \
            f"Star growth score ({score_stars}) should be higher than citation growth ({score_citations})"

    def test_score_bounds(self):
        """Test that score is always between 0 and 10."""
        test_cases = [
            # Extreme growth
            (10000, 1000, 1, 1, 1),
            # Negative growth (shouldn't happen but test boundary)
            (50, 5, 100, 10, 365),
            # Zero everything
            (0, 0, 0, 0, 0),
            # Very old paper
            (1000, 100, 100, 10, 1000),
        ]

        for stars_new, cites_new, stars_old, cites_old, age in test_cases:
            score = calculate_hype_score(stars_new, cites_new, stars_old, cites_old, age)
            assert 0 <= score <= 10, \
                f"Score {score} out of bounds for case ({stars_new}, {cites_new}, {stars_old}, {cites_old}, {age})"

    def test_normalization_prevents_overflow(self):
        """Test that very large absolute values are normalized properly."""
        score = calculate_hype_score(
            current_stars=50000,  # Way above max
            current_citations=5000,  # Way above max
            old_stars=40000,
            old_citations=4000,
            paper_age_days=30,
            max_stars=10000,
            max_citations=1000
        )

        # Should still be in valid range despite huge numbers
        assert 0 <= score <= 10, f"Normalization failed, score {score} out of range"


class TestHypeScoreEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_same_day_comparison(self):
        """Test score when comparing metrics from same day."""
        score = calculate_hype_score(
            current_stars=100,
            current_citations=10,
            old_stars=100,
            old_citations=10,
            paper_age_days=0
        )

        # Should handle same-day gracefully
        assert isinstance(score, float), "Score should be a float"
        assert 0 <= score <= 10, "Score should be in valid range"

    def test_negative_age_handled(self):
        """Test that negative age (future date) doesn't break calculation."""
        score = calculate_hype_score(
            current_stars=100,
            current_citations=10,
            old_stars=50,
            old_citations=5,
            paper_age_days=-1  # Invalid but shouldn't crash
        )

        # Should not crash, might give extra recency bonus
        assert 0 <= score <= 10, "Score should be in valid range even with negative age"

    def test_decimal_precision(self):
        """Test that scores are rounded to 2 decimal places."""
        score = calculate_hype_score(
            current_stars=123,
            current_citations=12,
            old_stars=100,
            old_citations=10,
            paper_age_days=45
        )

        # Check decimal places
        score_str = str(score)
        if '.' in score_str:
            decimal_places = len(score_str.split('.')[1])
            assert decimal_places <= 2, f"Score {score} has more than 2 decimal places"
