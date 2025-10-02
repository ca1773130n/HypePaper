"""Contract test for GET /api/v1/papers endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_papers_returns_200(client: AsyncClient):
    """Test that GET /api/v1/papers returns 200 status code."""
    response = await client.get("/api/v1/papers")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_papers_returns_papers_array(client: AsyncClient):
    """Test that response contains papers array and pagination info."""
    response = await client.get("/api/v1/papers")
    data = response.json()

    assert "papers" in data
    assert isinstance(data["papers"], list)
    assert "total" in data
    assert isinstance(data["total"], int)
    assert "limit" in data
    assert "offset" in data


@pytest.mark.asyncio
async def test_get_papers_accepts_topic_filter(client: AsyncClient):
    """Test that endpoint accepts topic_id query parameter."""
    topic_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(f"/api/v1/papers?topic_id={topic_id}")

    assert response.status_code == 200
    data = response.json()
    assert "papers" in data


@pytest.mark.asyncio
async def test_get_papers_accepts_sort_parameter(client: AsyncClient):
    """Test that endpoint accepts sort query parameter."""
    for sort_option in ["hype_score", "recency", "stars"]:
        response = await client.get(f"/api/v1/papers?sort={sort_option}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_papers_rejects_invalid_sort(client: AsyncClient):
    """Test that endpoint rejects invalid sort parameter."""
    response = await client.get("/api/v1/papers?sort=invalid")
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_papers_accepts_pagination(client: AsyncClient):
    """Test that endpoint accepts limit and offset parameters."""
    response = await client.get("/api/v1/papers?limit=10&offset=0")
    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["papers"]) <= 10


@pytest.mark.asyncio
async def test_get_papers_paper_schema(client: AsyncClient):
    """Test that each paper matches expected schema."""
    response = await client.get("/api/v1/papers?limit=1")
    data = response.json()

    if len(data["papers"]) > 0:
        paper = data["papers"][0]

        # Required fields from PaperSummary schema
        assert "id" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "published_date" in paper
        assert "hype_score" in paper

        # Field types
        assert isinstance(paper["id"], str)
        assert isinstance(paper["title"], str)
        assert isinstance(paper["authors"], list)
        assert len(paper["authors"]) >= 1
        assert isinstance(paper["hype_score"], (int, float))
        assert 0 <= paper["hype_score"] <= 100

        # Trend label
        if "trend_label" in paper:
            assert paper["trend_label"] in ["rising", "stable", "declining"]
