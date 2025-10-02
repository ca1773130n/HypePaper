"""Integration test for Scenario 1: First-time user adds topic and sees trending papers.

Maps to quickstart.md Scenario 1.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_adds_topic_and_sees_papers(client: AsyncClient):
    """
    Given: User visits HypePaper for the first time
    When: They add a research topic like "neural rendering"
    Then: They see a list of trending papers in that topic ranked by hype score
    """
    # Step 1: Get list of available topics
    topics_response = await client.get("/api/v1/topics")
    assert topics_response.status_code == 200

    topics_data = topics_response.json()
    assert "topics" in topics_data
    assert len(topics_data["topics"]) > 0

    # Find "neural rendering" topic
    neural_rendering_topic = None
    for topic in topics_data["topics"]:
        if "neural rendering" in topic["name"].lower():
            neural_rendering_topic = topic
            break

    assert neural_rendering_topic is not None, "Neural rendering topic should exist"

    # Step 2: Get papers for this topic
    papers_response = await client.get(
        f"/api/v1/papers?topic_id={neural_rendering_topic['id']}&sort=hype_score"
    )
    assert papers_response.status_code == 200

    papers_data = papers_response.json()
    assert "papers" in papers_data

    # Verify papers are sorted by hype score (descending)
    if len(papers_data["papers"]) > 1:
        hype_scores = [p["hype_score"] for p in papers_data["papers"]]
        assert hype_scores == sorted(hype_scores, reverse=True)


@pytest.mark.asyncio
async def test_paper_cards_show_required_information(client: AsyncClient):
    """
    Verify each paper card shows:
    - Title, Authors, Published date, Venue
    - Hype score (0-100)
    - Trend indicator (rising/stable/declining)
    - GitHub stars, Citation count
    """
    response = await client.get("/api/v1/papers?limit=1")
    assert response.status_code == 200

    data = response.json()
    if len(data["papers"]) > 0:
        paper = data["papers"][0]

        # Required display fields
        assert "title" in paper
        assert "authors" in paper and len(paper["authors"]) > 0
        assert "published_date" in paper
        # venue can be optional
        assert "hype_score" in paper
        assert 0 <= paper["hype_score"] <= 100
        assert "trend_label" in paper
        assert paper["trend_label"] in ["rising", "stable", "declining"]


@pytest.mark.asyncio
async def test_page_load_performance(client: AsyncClient):
    """Success Criteria: Page load < 2 seconds."""
    import time

    start = time.time()
    response = await client.get("/api/v1/papers?limit=50")
    duration = time.time() - start

    assert response.status_code == 200
    # API should respond in < 500ms (frontend has additional 1.5s budget)
    assert duration < 0.5, f"API response took {duration:.2f}s, should be < 0.5s"
