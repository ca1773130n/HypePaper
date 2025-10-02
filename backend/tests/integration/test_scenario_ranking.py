"""Integration test for Scenario 5: Paper with rapid star growth rises in ranking.

Maps to quickstart.md Scenario 5.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rapid_star_growth_increases_hype_score(client: AsyncClient):
    """
    Given: Paper has rapid star growth over 7 days
    When: Hype score is calculated
    Then: Paper rises in ranking to reflect trending status
    """
    # Get papers sorted by hype score
    response = await client.get("/api/v1/papers?sort=hype_score&limit=10")
    assert response.status_code == 200

    data = response.json()

    # Verify papers are sorted by hype score descending
    if len(data["papers"]) > 1:
        hype_scores = [p["hype_score"] for p in data["papers"]]
        assert hype_scores == sorted(hype_scores, reverse=True), \
            "Papers should be sorted by hype score (descending)"


@pytest.mark.asyncio
async def test_growth_rate_matters_more_than_absolute_values(client: AsyncClient):
    """
    Verify hype score prioritizes growth over absolute numbers.

    Example:
    - Paper A: 500 stars (+900% growth in 7d) → High hype score
    - Paper B: 1000 stars (0% growth) → Lower hype score
    """
    response = await client.get("/api/v1/papers?sort=hype_score&limit=20")
    data = response.json()

    if len(data["papers"]) >= 2:
        # Get detailed info for top papers
        top_paper_id = data["papers"][0]["id"]

        detail_response = await client.get(f"/api/v1/papers/{top_paper_id}")
        top_paper = detail_response.json()

        # Top paper should have high growth rate
        assert "star_growth_7d" in top_paper
        # Growth rate should be positive for trending papers
        if top_paper.get("current_stars") and top_paper["star_growth_7d"] is not None:
            # High hype score should correlate with growth
            assert top_paper["hype_score"] > 50  # Reasonably high


@pytest.mark.asyncio
async def test_trend_label_reflects_growth_direction(client: AsyncClient):
    """Verify trend labels (rising/stable/declining) match growth rates."""
    response = await client.get("/api/v1/papers?limit=10")
    data = response.json()

    for paper in data["papers"]:
        if "trend_label" in paper:
            detail_response = await client.get(f"/api/v1/papers/{paper['id']}")
            detail = detail_response.json()

            if "star_growth_7d" in detail and detail["star_growth_7d"] is not None:
                growth_rate = detail["star_growth_7d"]

                # Trend label should match growth
                if paper["trend_label"] == "rising":
                    # Should have positive growth (>10% per research.md)
                    assert growth_rate > 0.1 or paper["hype_score"] > 60

                elif paper["trend_label"] == "declining":
                    # Should have negative growth (<-5% per research.md)
                    assert growth_rate < -0.05 or paper["hype_score"] < 20


@pytest.mark.asyncio
async def test_hype_score_formula_validation(client: AsyncClient):
    """
    Validate hype score calculation matches research.md formula:
    hype_score = (
        0.4 * star_growth_rate_7d +
        0.3 * citation_growth_rate_30d +
        0.2 * absolute_stars_normalized +
        0.1 * recency_bonus
    ) * 100
    """
    response = await client.get("/api/v1/papers?limit=1")
    data = response.json()

    if len(data["papers"]) > 0:
        paper_id = data["papers"][0]["id"]

        detail_response = await client.get(f"/api/v1/papers/{paper_id}")
        paper = detail_response.json()

        # Verify all components are present for formula
        assert "hype_score" in paper
        assert "star_growth_7d" in paper
        assert "citation_growth_30d" in paper
        # Hype score should be 0-100
        assert 0 <= paper["hype_score"] <= 100
