"""Contract tests for Jobs API."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_post_crawl_job(client: AsyncClient):
    response = await client.post("/api/v1/jobs/crawl", json={
        "source": "arxiv",
        "arxiv_keywords": "transformer",
        "arxiv_max_results": 10
    })
    assert response.status_code in [202, 503]

@pytest.mark.asyncio
async def test_get_job_status(client: AsyncClient):
    job_id = "test-job-id"
    response = await client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code in [200, 404]
