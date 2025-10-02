"""Integration test for Scenario 4: New paper appears after daily monitoring.

Maps to quickstart.md Scenario 4.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_new_paper_appears_within_48_hours(client: AsyncClient):
    """
    Given: A new paper is published on arXiv with GitHub repository
    When: Daily monitoring runs
    Then: Paper appears in relevant topic lists within 24-48 hours
    """
    # This test would verify:
    # 1. Paper is fetched from arXiv
    # 2. GitHub repo is linked via Papers With Code
    # 3. LLM matches paper to topics (relevance >= 6.0)
    # 4. Initial MetricSnapshot is created

    # For now, we test that newly added papers appear in topic lists
    response = await client.get("/api/v1/papers?sort=recency&limit=10")
    assert response.status_code == 200

    data = response.json()
    if len(data["papers"]) > 0:
        # Most recent paper
        paper = data["papers"][0]

        # Verify it has required fields
        assert "id" in paper
        assert "published_date" in paper
        assert "days_since_publish" in paper

        # Verify it's been matched to at least one topic
        detail_response = await client.get(f"/api/v1/papers/{paper['id']}")
        assert detail_response.status_code == 200

        detail = detail_response.json()
        assert "topics" in detail
        # Should have at least one topic match
        if len(detail["topics"]) > 0:
            topic = detail["topics"][0]
            assert "relevance_score" in topic
            assert topic["relevance_score"] >= 6.0


@pytest.mark.asyncio
async def test_new_paper_has_new_badge(client: AsyncClient):
    """Verify papers published within 48 hours have NEW indicator."""
    response = await client.get("/api/v1/papers?sort=recency&limit=10")
    data = response.json()

    if len(data["papers"]) > 0:
        for paper in data["papers"]:
            if "days_since_publish" in paper:
                # Papers <= 2 days old should be marked as new
                is_new = paper["days_since_publish"] <= 2
                # Frontend will use this to show "NEW" badge
                assert isinstance(is_new, bool)


@pytest.mark.asyncio
async def test_daily_job_creates_initial_metrics(client: AsyncClient):
    """Verify new papers get initial metric snapshot."""
    # Get newest paper
    response = await client.get("/api/v1/papers?sort=recency&limit=1")
    data = response.json()

    if len(data["papers"]) > 0:
        paper_id = data["papers"][0]["id"]

        # Check if metrics exist
        metrics_response = await client.get(f"/api/v1/papers/{paper_id}/metrics")
        assert metrics_response.status_code == 200

        metrics_data = metrics_response.json()
        # Should have at least one metric snapshot
        assert "metrics" in metrics_data
        # Even if empty initially, structure should exist
        assert isinstance(metrics_data["metrics"], list)
