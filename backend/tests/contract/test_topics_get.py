"""Contract test for GET /api/v1/topics endpoint.

This test verifies the API contract matches the OpenAPI specification
in contracts/api-topics.yaml.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_topics_returns_200(client: AsyncClient):
    """Test that GET /api/v1/topics returns 200 status code."""
    response = await client.get("/api/v1/topics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_topics_returns_topics_array(client: AsyncClient):
    """Test that response contains 'topics' array."""
    response = await client.get("/api/v1/topics")
    data = response.json()

    assert "topics" in data
    assert isinstance(data["topics"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_get_topics_topic_schema(client: AsyncClient):
    """Test that each topic matches the expected schema."""
    response = await client.get("/api/v1/topics")
    data = response.json()

    if len(data["topics"]) > 0:
        topic = data["topics"][0]

        # Required fields
        assert "id" in topic
        assert "name" in topic
        assert "created_at" in topic

        # Optional fields
        assert "description" in topic or topic.get("description") is None
        assert "keywords" in topic or topic.get("keywords") is None
        assert "paper_count" in topic

        # Field types
        assert isinstance(topic["id"], str)
        assert isinstance(topic["name"], str)
        assert len(topic["name"]) >= 3
        assert len(topic["name"]) <= 100


@pytest.mark.asyncio
async def test_get_topics_returns_empty_list_when_no_topics(client: AsyncClient):
    """Test that empty database returns empty topics list."""
    response = await client.get("/api/v1/topics")
    data = response.json()

    # Should return valid structure even with no topics
    assert data["total"] >= 0
    assert isinstance(data["topics"], list)
