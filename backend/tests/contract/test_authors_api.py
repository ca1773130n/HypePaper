"""Contract tests for Author API endpoints.

Tests the API contracts defined in contracts/authors-api.yaml.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_author(async_client: AsyncClient, test_author_id: int):
    """Test GET /api/authors/{author_id}.

    Contract: Response 200 with AuthorDetail schema
    - id, name, primary_affiliation, affiliation_history, paper_count,
      total_citation_count, email, website_url, latest_paper, recent_papers
    """
    response = await async_client.get(f"/api/authors/{test_author_id}")

    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "id" in data
    assert "name" in data
    assert "paper_count" in data
    assert "total_citation_count" in data

    # Optional/nullable fields
    assert "primary_affiliation" in data
    assert "affiliation_history" in data
    assert "email" in data
    assert "website_url" in data
    assert "latest_paper" in data
    assert "recent_papers" in data
    assert isinstance(data["recent_papers"], list)


@pytest.mark.asyncio
async def test_get_author_not_found(async_client: AsyncClient):
    """Test GET /api/authors/{author_id} with non-existent ID.

    Contract: Returns 404 Not Found
    """
    response = await async_client.get("/api/authors/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_authors(async_client: AsyncClient):
    """Test GET /api/authors/search?q={query}.

    Contract: Response 200 with array of AuthorSummary
    - Each: id, name, primary_affiliation, paper_count
    """
    response = await async_client.get("/api/authors/search?q=test&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        author = data[0]
        assert "id" in author
        assert "name" in author
        assert "paper_count" in author


@pytest.mark.asyncio
async def test_search_authors_min_query_length(async_client: AsyncClient):
    """Test GET /api/authors/search with query < 2 characters.

    Contract: Returns 422 Unprocessable Entity
    """
    response = await async_client.get("/api/authors/search?q=a")
    assert response.status_code == 422
