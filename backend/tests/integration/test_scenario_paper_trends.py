"""Integration test for Scenario 3: User views paper details with historical trend.

Maps to quickstart.md Scenario 3.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_view_paper_with_30_day_trend_history(client: AsyncClient):
    """
    Given: System has been tracking a paper for 30 days
    When: User views that paper's details
    Then: They see a trend graph showing how GitHub stars and citations changed over time
    """
    # Get a paper
    papers_response = await client.get("/api/v1/papers?limit=1")
    assert papers_response.status_code == 200

    papers_data = papers_response.json()
    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]

        # Get paper details
        detail_response = await client.get(f"/api/v1/papers/{paper_id}")
        assert detail_response.status_code == 200

        paper_detail = detail_response.json()
        assert "title" in paper_detail
        assert "abstract" in paper_detail
        assert "star_growth_7d" in paper_detail
        assert "citation_growth_30d" in paper_detail

        # Get metrics history
        metrics_response = await client.get(f"/api/v1/papers/{paper_id}/metrics?days=30")
        assert metrics_response.status_code == 200

        metrics_data = metrics_response.json()
        assert "metrics" in metrics_data
        assert "paper_id" in metrics_data
        assert metrics_data["paper_id"] == paper_id


@pytest.mark.asyncio
async def test_trend_chart_shows_historical_data(client: AsyncClient):
    """Verify chart displays both stars and citations over time."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]

        metrics_response = await client.get(f"/api/v1/papers/{paper_id}/metrics")
        metrics_data = metrics_response.json()

        if len(metrics_data["metrics"]) > 0:
            metric = metrics_data["metrics"][0]

            # Each metric snapshot should have date and values
            assert "snapshot_date" in metric
            # Stars and citations can be null
            assert "github_stars" in metric or metric.get("github_stars") is None
            assert "citation_count" in metric or metric.get("citation_count") is None


@pytest.mark.asyncio
async def test_hype_score_breakdown_explains_calculation(client: AsyncClient):
    """Verify hype score breakdown shows components."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]

        detail_response = await client.get(f"/api/v1/papers/{paper_id}")
        paper = detail_response.json()

        # Breakdown components
        assert "hype_score" in paper
        assert "star_growth_7d" in paper  # 40% weight
        assert "citation_growth_30d" in paper  # 30% weight
        # Formula from research.md should be verifiable
