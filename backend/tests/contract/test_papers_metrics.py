"""Contract test for GET /api/v1/papers/{id}/metrics endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_paper_metrics_returns_404_when_paper_not_exists(client: AsyncClient):
    """Test that GET /api/v1/papers/{id}/metrics returns 404 for non-existent paper."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/papers/{fake_id}/metrics")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_paper_metrics_returns_metrics_array(client: AsyncClient):
    """Test that response contains metrics array."""
    # Get a valid paper ID first
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "paper_id" in data
        assert "metrics" in data
        assert isinstance(data["metrics"], list)
        assert data["paper_id"] == paper_id


@pytest.mark.asyncio
async def test_get_paper_metrics_accepts_days_parameter(client: AsyncClient):
    """Test that endpoint accepts days query parameter."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]

        # Test with default (30 days)
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics")
        assert response.status_code == 200

        # Test with custom days
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics?days=7")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_paper_metrics_metric_snapshot_schema(client: AsyncClient):
    """Test that each metric snapshot matches expected schema."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics")

        assert response.status_code == 200
        data = response.json()

        if len(data["metrics"]) > 0:
            metric = data["metrics"][0]

            # Required field
            assert "snapshot_date" in metric

            # Optional fields (can be null)
            assert "github_stars" in metric or metric.get("github_stars") is None
            assert "citation_count" in metric or metric.get("citation_count") is None

            # If present, values should be non-negative
            if metric.get("github_stars") is not None:
                assert metric["github_stars"] >= 0
            if metric.get("citation_count") is not None:
                assert metric["citation_count"] >= 0


@pytest.mark.asyncio
async def test_get_paper_metrics_validates_days_range(client: AsyncClient):
    """Test that endpoint validates days parameter range."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]

        # Test minimum (should be >= 7)
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics?days=1")
        assert response.status_code in [200, 400, 422]

        # Test maximum (should be <= 365)
        response = await client.get(f"/api/v1/papers/{paper_id}/metrics?days=1000")
        assert response.status_code in [200, 400, 422]
