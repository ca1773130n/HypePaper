"""Contract tests for GitHub API."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_github_metrics(client: AsyncClient, test_paper_id: str):
    response = await client.get(f"/api/v1/github/metrics/{test_paper_id}")
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_get_trending_papers(client: AsyncClient):
    response = await client.get("/api/v1/github/trending?metric=weekly_hype&limit=50")
    assert response.status_code == 200
