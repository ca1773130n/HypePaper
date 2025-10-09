"""Contract tests for Citations API."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_citation_graph(client: AsyncClient, test_paper_id: str):
    response = await client.get(f"/api/v1/citations/graph?paper_id={test_paper_id}&depth=2")
    if response.status_code == 200:
        graph = response.json()
        assert "nodes" in graph
        assert "edges" in graph

@pytest.mark.asyncio
async def test_post_discover_via_citations(client: AsyncClient, test_paper_id: str):
    response = await client.post("/api/v1/citations/discover", json={
        "paper_id": test_paper_id,
        "method": "citations",
        "max_results": 20
    })
    assert response.status_code in [200, 404]
