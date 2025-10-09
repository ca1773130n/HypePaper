"""Contract tests for Papers API - validates OpenAPI spec compliance."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_papers_returns_extended_schema(client: AsyncClient):
    """Test GET /api/v1/papers returns extended schema with legacy fields."""
    response = await client.get("/api/v1/papers")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data

    if len(data["items"]) > 0:
        paper = data["items"][0]

        # Core fields
        assert "id" in paper
        assert "title" in paper
        assert "authors" in paper

        # Extended legacy fields
        assert "primary_task" in paper
        assert "datasets_used" in paper
        assert "github_star_count" in paper
        assert "citations_total" in paper


@pytest.mark.asyncio
async def test_get_papers_with_filters(client: AsyncClient):
    """Test GET /api/v1/papers with extended filter parameters."""
    response = await client.get(
        "/api/v1/papers",
        params={
            "primary_task": "image segmentation",
            "min_github_stars": 10,
            "year": 2024,
            "limit": 20
        }
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_paper_by_id(client: AsyncClient, test_paper_id: str):
    """Test GET /api/v1/papers/{id} returns full metadata."""
    response = await client.get(f"/api/v1/papers/{test_paper_id}")
    assert response.status_code == 200

    paper = response.json()
    assert paper["id"] == test_paper_id
    assert "title" in paper
    assert "abstract" in paper


@pytest.mark.asyncio
async def test_get_paper_citations(client: AsyncClient, test_paper_id: str):
    """Test GET /api/v1/papers/{id}/citations returns citation relationships."""
    response = await client.get(f"/api/v1/papers/{test_paper_id}/citations")
    assert response.status_code == 200

    citations = response.json()
    assert "cites" in citations
    assert "cited_by" in citations
    assert isinstance(citations["cites"], list)
    assert isinstance(citations["cited_by"], list)


@pytest.mark.asyncio
async def test_get_paper_github_metrics(client: AsyncClient, test_paper_id: str):
    """Test GET /api/v1/papers/{id}/github returns GitHub metrics."""
    response = await client.get(f"/api/v1/papers/{test_paper_id}/github")

    # May return 404 if no GitHub metrics exist
    if response.status_code == 200:
        metrics = response.json()
        assert "repo_url" in metrics
        assert "current_stars" in metrics
        assert "hype_scores" in metrics
        assert "star_history" in metrics
    else:
        assert response.status_code == 404
