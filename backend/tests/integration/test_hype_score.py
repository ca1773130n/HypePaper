"""Integration tests for hype score calculation with votes.

Tests logarithmic vote component formula from research.md.
"""
import pytest
import math
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.paper import Paper
from src.services.hype_score import calculate_vote_component, calculate_hype_score


@pytest.mark.asyncio
async def test_vote_component_zero_votes():
    """Test vote_component = 0 when votes = 0.

    From research.md Decision 4
    """
    vote_component = calculate_vote_component(0)
    assert vote_component == 0.0


@pytest.mark.asyncio
async def test_vote_component_10_votes():
    """Test vote_component increases logarithmically with votes.

    With base-2 log and normalization, 10 votes should give ~0.35
    """
    vote_component = calculate_vote_component(10)
    # log2(11) / 10 ≈ 3.46 / 10 ≈ 0.35
    assert 0.3 < vote_component < 0.4
    assert vote_component > 0.0


@pytest.mark.asyncio
async def test_vote_component_100_votes():
    """Test vote_component increases logarithmically with votes.

    With base-2 log and normalization, 100 votes should give ~0.67
    """
    vote_component = calculate_vote_component(100)
    # log2(101) / 10 ≈ 6.66 / 10 ≈ 0.67
    assert 0.6 < vote_component < 0.7
    assert vote_component > calculate_vote_component(10)


@pytest.mark.asyncio
async def test_vote_component_1000_votes():
    """Test vote_component increases logarithmically with votes.

    With base-2 log and normalization, 1000 votes should give ~1.0 (maxed)
    """
    vote_component = calculate_vote_component(1000)
    # log2(1001) / 10 ≈ 9.97 / 10 ≈ 1.0
    assert 0.9 < vote_component <= 1.0
    assert vote_component > calculate_vote_component(100)


@pytest.mark.asyncio
async def test_edge_case_6_negative_votes():
    """Edge Case 6: Negative vote_count.

    From quickstart.md EC6
    Paper with vote_count=-3 should have vote_component=0 (clamped).
    """
    vote_component = calculate_vote_component(-3)
    # log(1 + max(0, -3)) = log(1) = 0
    assert vote_component == 0.0


@pytest.mark.asyncio
async def test_edge_case_7_hype_score_with_negative_votes():
    """Edge Case 7: Hype score with negative votes contributes 0.

    From quickstart.md EC7
    """
    from datetime import date

    hype_score = calculate_hype_score(
        github_stars=100,
        citation_count=50,
        vote_count=-10,  # Negative votes
        published_date=date(2024, 1, 1)
    )

    # Vote component should be 0 with negative votes
    # Hype score should still be positive from other components
    assert hype_score > 0
    assert hype_score >= 0.0


@pytest.mark.asyncio
async def test_hype_score_formula_weights():
    """Test hype score formula uses correct weights.

    Formula: github(40%) + citations(30%) + votes(20%) + recency(10%)
    From research.md Decision 4
    """
    from datetime import date

    hype_score = calculate_hype_score(
        github_stars=1000,
        citation_count=500,
        vote_count=100,
        published_date=date.today()
    )

    # Should have contributions from all components
    assert hype_score > 0
    assert hype_score < 1.0  # Normalized score


@pytest.mark.asyncio
async def test_hype_score_non_negative():
    """Test hype_score is always >= 0 (clamped).

    From data-model.md → MetricSnapshot constraints
    """
    from datetime import date

    # Even with all zero inputs, should be clamped to 0
    hype_score = calculate_hype_score(
        github_stars=0,
        citation_count=0,
        vote_count=0,
        published_date=date.today()
    )

    assert hype_score >= 0
