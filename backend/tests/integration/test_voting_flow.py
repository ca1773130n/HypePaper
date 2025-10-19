"""Integration tests for voting flow.

Tests end-to-end voting scenarios from quickstart.md.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_voting_scenario_3_upvote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Scenario 3: User upvotes paper → vote_count increases.

    From quickstart.md Scenario 3
    """
    # Get initial vote count
    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    initial_vote_count = paper_response.json()["vote_count"]

    # User clicks upvote button
    vote_response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )
    assert vote_response.status_code == 200

    # Verify vote_count increased by 1
    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    new_vote_count = paper_response.json()["vote_count"]
    assert new_vote_count == initial_vote_count + 1

    # Verify vote status shows upvote
    status_response = await async_client.get(
        f"/api/papers/{test_paper_id}/vote/status",
        headers=auth_headers
    )
    assert status_response.json()["vote_type"] == "upvote"


@pytest.mark.asyncio
async def test_voting_scenario_4_remove_vote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Scenario 4: User removes upvote → vote_count decreases.

    From quickstart.md Scenario 4
    """
    # User upvotes first
    await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    vote_count_with_upvote = paper_response.json()["vote_count"]

    # User clicks upvote button again (toggle off)
    remove_response = await async_client.delete(
        f"/api/papers/{test_paper_id}/vote",
        headers=auth_headers
    )
    assert remove_response.status_code == 204

    # Verify vote_count decreased by 1
    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    new_vote_count = paper_response.json()["vote_count"]
    assert new_vote_count == vote_count_with_upvote - 1


@pytest.mark.asyncio
async def test_voting_scenario_5_change_vote(async_client: AsyncClient, auth_headers: dict, test_paper_id: str):
    """Scenario 5: User changes upvote to downvote → vote_count changes by 2.

    From quickstart.md Scenario 5
    """
    # User upvotes
    await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )

    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    vote_count_with_upvote = paper_response.json()["vote_count"]

    # User changes to downvote
    await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "downvote"},
        headers=auth_headers
    )

    # Verify vote_count decreased by 2 (from +1 to -1)
    paper_response = await async_client.get(f"/api/papers/{test_paper_id}")
    new_vote_count = paper_response.json()["vote_count"]
    assert new_vote_count == vote_count_with_upvote - 2


@pytest.mark.asyncio
async def test_edge_case_3_voting_without_auth(async_client: AsyncClient, test_paper_id: str):
    """Edge Case 3: Unauthenticated user cannot vote (401).

    From quickstart.md EC3
    """
    response = await async_client.post(
        f"/api/papers/{test_paper_id}/vote",
        json={"vote_type": "upvote"}
        # No auth_headers
    )
    assert response.status_code == 401
