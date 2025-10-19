"""Contract tests for Vote API endpoints.

Tests the API contracts defined in contracts/votes-api.yaml.
These tests verify request/response schemas and error handling.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_cast_vote_upvote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test POST /api/papers/{paper_id}/vote with upvote.

    Contract: POST /api/papers/{id}/vote
    - Request: {"vote_type": "upvote"}
    - Response 200: {"vote_type": "upvote", "vote_count": int, "created_at": str, "updated_at": str}
    - Requires authentication
    """
    response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response schema
    assert "vote_type" in data
    assert data["vote_type"] == "upvote"
    assert "vote_count" in data
    assert isinstance(data["vote_count"], int)
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_cast_vote_downvote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test POST /api/papers/{paper_id}/vote with downvote.

    Contract: vote_type can be "downvote"
    """
    response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "downvote"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["vote_type"] == "downvote"


@pytest.mark.asyncio
async def test_cast_vote_unauthorized(async_client: AsyncClient, test_paper_id: str):
    """Test POST /api/papers/{paper_id}/vote without authentication.

    Contract: Returns 401 Unauthorized when no auth token provided
    """
    response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"}
        # No auth_headers
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cast_vote_invalid_paper(async_client: AsyncClient, auth_headers: dict):
    """Test POST /api/papers/{paper_id}/vote with non-existent paper.

    Contract: Returns 404 Not Found for invalid paper_id
    """
    fake_paper_id = str(uuid4())
    response = await async_client.post(
        f"/api/papers/{fake_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cast_vote_invalid_type(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test POST /api/papers/{paper_id}/vote with invalid vote_type.

    Contract: Returns 422 Unprocessable Entity for invalid vote_type
    """
    response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "invalid"},
        headers=auth_headers
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_remove_vote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test DELETE /api/papers/{paper_id}/vote.

    Contract: DELETE /api/papers/{id}/vote
    - Response 204: No content
    - Requires authentication
    """
    # First cast a vote
    await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    # Then remove it
    response = await async_client.delete(
        f"/api/papers/{test_paper_id}/vote",
        headers=auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_vote_unauthorized(async_client: AsyncClient, test_paper_id: str):
    """Test DELETE /api/papers/{paper_id}/vote without authentication.

    Contract: Returns 401 Unauthorized
    """
    response = await async_client.delete(
        f"/api/papers/{test_paper_id}/vote"
        # No auth_headers
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_vote_not_found(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test DELETE /api/papers/{paper_id}/vote when no vote exists.

    Contract: Returns 404 Not Found
    """
    response = await async_client.delete(
        f"/api/papers/{test_paper_id}/vote",
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_vote_status(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/vote/status.

    Contract: GET /api/papers/{id}/vote/status
    - Response 200: {"has_voted": bool, "vote_type": str|null, "created_at": str|null}
    - Requires authentication
    """
    # Cast a vote first
    await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    response = await async_client.get(
        f"/api/papers/{test_paper_id}/vote/status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response schema
    assert "has_voted" in data
    assert isinstance(data["has_voted"], bool)
    assert data["has_voted"] is True
    assert "vote_type" in data
    assert data["vote_type"] in ["upvote", "downvote", None]
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_vote_status_no_vote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/vote/status when user hasn't voted.

    Contract: has_voted=false, vote_type=null
    """
    response = await async_client.get(
        f"/api/papers/{test_paper_id}/vote/status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_voted"] is False
    assert data["vote_type"] is None
    assert data["created_at"] is None


@pytest.mark.asyncio
async def test_get_vote_status_unauthorized(async_client: AsyncClient, test_paper_id: str):
    """Test GET /api/papers/{paper_id}/vote/status without authentication.

    Contract: Returns 401 Unauthorized
    """
    response = await async_client.get(
        f"/api/papers/{test_paper_id}/vote/status"
        # No auth_headers
    )

    assert response.status_code == 401
