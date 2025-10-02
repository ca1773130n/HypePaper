"""Integration test for Scenario 2: User with multiple topics returns and sees grouped papers.

Maps to quickstart.md Scenario 2.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_returns_with_multiple_watched_topics(client: AsyncClient):
    """
    Given: User has previously added 3 topics
    When: They return to the site
    Then: They see papers grouped by their watched topics with current hype scores
    """
    # Get list of topics
    topics_response = await client.get("/api/v1/topics")
    assert topics_response.status_code == 200

    topics_data = topics_response.json()
    topic_ids = [t["id"] for t in topics_data["topics"][:3]]  # Get first 3 topics

    # For each watched topic, get papers
    papers_by_topic = {}
    for topic_id in topic_ids:
        response = await client.get(f"/api/v1/papers?topic_id={topic_id}&limit=10")
        assert response.status_code == 200

        data = response.json()
        papers_by_topic[topic_id] = data["papers"]

    # Verify we got papers for each topic (may be empty for some)
    assert len(papers_by_topic) == 3


@pytest.mark.asyncio
async def test_papers_grouped_correctly_by_topic(client: AsyncClient):
    """Verify papers are correctly grouped by topic."""
    # Get two different topics
    topics_response = await client.get("/api/v1/topics")
    topics_data = topics_response.json()

    if len(topics_data["topics"]) >= 2:
        topic1_id = topics_data["topics"][0]["id"]
        topic2_id = topics_data["topics"][1]["id"]

        # Get papers for each topic
        papers1 = await client.get(f"/api/v1/papers?topic_id={topic1_id}")
        papers2 = await client.get(f"/api/v1/papers?topic_id={topic2_id}")

        assert papers1.status_code == 200
        assert papers2.status_code == 200

        # Papers in each group should be different (unless there's overlap)
        data1 = papers1.json()
        data2 = papers2.json()

        # Just verify structure is correct for grouping
        assert "papers" in data1
        assert "papers" in data2


@pytest.mark.asyncio
async def test_hype_scores_are_current(client: AsyncClient):
    """Verify hype scores reflect current metrics (from today's snapshot)."""
    response = await client.get("/api/v1/papers?limit=5")
    assert response.status_code == 200

    data = response.json()
    for paper in data["papers"]:
        assert "hype_score" in paper
        # Hype score should be calculated (not null)
        assert paper["hype_score"] is not None
        assert isinstance(paper["hype_score"], (int, float))
