"""Contract test for GET /api/v1/papers/{id} endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_paper_by_id_returns_404_when_not_exists(client: AsyncClient):
    """Test that GET /api/v1/papers/{id} returns 404 for non-existent paper."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/papers/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_paper_by_id_returns_paper_detail_schema(client: AsyncClient):
    """Test that response matches PaperDetail schema when paper exists."""
    # First get list of papers to find a valid ID
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]
        response = await client.get(f"/api/v1/papers/{paper_id}")

        assert response.status_code == 200
        paper = response.json()

        # PaperDetail extends PaperSummary with additional fields
        assert "id" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "abstract" in paper  # Additional field
        assert "topics" in paper  # Additional field
        assert "star_growth_7d" in paper  # Additional field
        assert "citation_growth_30d" in paper  # Additional field

        # Verify topics structure
        if len(paper["topics"]) > 0:
            topic = paper["topics"][0]
            assert "id" in topic
            assert "name" in topic
            assert "relevance_score" in topic
            assert 0 <= topic["relevance_score"] <= 10


@pytest.mark.asyncio
async def test_get_paper_by_id_includes_arxiv_and_github_links(client: AsyncClient):
    """Test that paper details include source links."""
    papers_response = await client.get("/api/v1/papers?limit=1")
    papers_data = papers_response.json()

    if len(papers_data["papers"]) > 0:
        paper_id = papers_data["papers"][0]["id"]
        response = await client.get(f"/api/v1/papers/{paper_id}")

        assert response.status_code == 200
        paper = response.json()

        # Links should be present (can be null)
        assert "arxiv_url" in paper
        assert "github_url" in paper
        assert "pdf_url" in paper
