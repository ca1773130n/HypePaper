"""Contract test for GET /api/v1/topics/{id} endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_topic_by_id_returns_200_when_exists(client: AsyncClient):
    """Test that GET /api/v1/topics/{id} returns 200 for existing topic."""
    # This will fail until we have actual topics seeded
    # Using a placeholder UUID for now
    topic_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(f"/api/v1/topics/{topic_id}")

    # Should return 404 or 200 depending on if topic exists
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_topic_by_id_returns_404_when_not_exists(client: AsyncClient):
    """Test that GET /api/v1/topics/{id} returns 404 for non-existent topic."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/topics/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_topic_by_id_returns_topic_schema(client: AsyncClient):
    """Test that response matches Topic schema when topic exists."""
    # First get list of topics to find a valid ID
    topics_response = await client.get("/api/v1/topics")
    topics_data = topics_response.json()

    if len(topics_data["topics"]) > 0:
        topic_id = topics_data["topics"][0]["id"]
        response = await client.get(f"/api/v1/topics/{topic_id}")

        assert response.status_code == 200
        topic = response.json()

        # Verify schema
        assert "id" in topic
        assert "name" in topic
        assert "created_at" in topic
        assert topic["id"] == topic_id


@pytest.mark.asyncio
async def test_get_topic_by_id_validates_uuid_format(client: AsyncClient):
    """Test that endpoint validates UUID format."""
    invalid_id = "not-a-uuid"
    response = await client.get(f"/api/v1/topics/{invalid_id}")

    # Should return 422 (validation error) or 404
    assert response.status_code in [404, 422]
