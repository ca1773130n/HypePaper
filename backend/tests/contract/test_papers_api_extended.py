"""Contract tests for extended Papers API endpoints.

Tests the API contracts defined in contracts/papers-api-extended.yaml.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_paper_includes_vote_count(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id} includes vote_count.

    Contract: Response includes vote_count field (integer)
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}")

    assert response.status_code == 200
    data = response.json()

    assert "vote_count" in data
    assert isinstance(data["vote_count"], int)


@pytest.mark.asyncio
async def test_get_paper_includes_enriched_fields(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id} includes enriched content fields.

    Contract: Response includes quick_summary, key_ideas, performance, limitations
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}")

    assert response.status_code == 200
    data = response.json()

    assert "quick_summary" in data
    assert "key_ideas" in data
    assert "quantitative_performance" in data
    assert "qualitative_performance" in data
    assert "limitations" in data


@pytest.mark.asyncio
async def test_get_paper_uses_published_date(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id} returns published_date not created_at.

    Contract: published_date is the actual paper publication date
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}")

    assert response.status_code == 200
    data = response.json()

    assert "published_date" in data
    assert "created_at" in data
    # published_date should exist and be a valid date string
    assert isinstance(data["published_date"], str)


@pytest.mark.asyncio
async def test_get_paper_metrics_time_series(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/metrics?days=30.

    Contract: Response is array of MetricSnapshot
    - Each: date, citation_count, github_stars, vote_count, hype_score
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}/metrics?days=30")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        snapshot = data[0]
        assert "date" in snapshot
        # All metrics are nullable
        assert "citation_count" in snapshot
        assert "github_stars" in snapshot
        assert "vote_count" in snapshot
        assert "hype_score" in snapshot


@pytest.mark.asyncio
async def test_get_paper_metrics_default_days(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/metrics without days parameter.

    Contract: Defaults to 30 days
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}/metrics")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should return up to 30 snapshots
    assert len(data) <= 30


@pytest.mark.asyncio
async def test_get_paper_metrics_custom_days(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/metrics?days=7.

    Contract: Returns metrics for specified number of days
    """
    response = await async_client.get(f"/api/papers/{test_paper_id}/metrics?days=7")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should return up to 7 snapshots
    assert len(data) <= 7
