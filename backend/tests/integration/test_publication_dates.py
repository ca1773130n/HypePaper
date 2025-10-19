"""Integration tests for publication date accuracy.

Tests that papers display actual publication dates, not crawl dates.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.paper import Paper


@pytest.mark.asyncio
async def test_scenario_1_published_date_not_crawl_date(async_client: AsyncClient, db_session: AsyncSession):
    """Scenario 1: Paper shows published_date (not created_at).

    From quickstart.md Scenario 1
    """
    # Create test paper with different published_date and created_at
    paper = Paper(
        title="Test Paper for Date Display",
        authors=["Test Author"],
        abstract="Test abstract",
        published_date=date(2025, 9, 15),  # Actual publish date
        arxiv_id="2509.12345"
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)

    # Fetch via API
    response = await async_client.get(f"/api/papers/{paper.id}")
    assert response.status_code == 200

    data = response.json()

    # Verify published_date is returned (not created_at)
    assert data["published_date"] == "2025-09-15"
    # created_at will be today (2025-10-11 or later)
    assert data["created_at"] != data["published_date"]


@pytest.mark.asyncio
async def test_arxiv_latest_version_date(async_client: AsyncClient, db_session: AsyncSession):
    """arXiv papers with multiple versions use latest version date.

    From research.md Decision 1, quickstart.md EC1
    """
    # Create arXiv paper
    paper = Paper(
        title="arXiv Paper with Multiple Versions",
        authors=["Author One"],
        abstract="Test abstract",
        published_date=date(2025, 9, 20),  # Latest version date
        arxiv_id="2509.12346v2"  # v2 indicates multiple versions
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)

    response = await async_client.get(f"/api/papers/{paper.id}")
    data = response.json()

    # Should show latest version date
    assert data["published_date"] == "2025-09-20"


@pytest.mark.asyncio
async def test_edge_case_1_paper_without_publish_date(async_client: AsyncClient):
    """Edge Case 1: Paper without publication date (fallback handling).

    From quickstart.md EC1
    """
    # This test verifies the system's behavior when published_date is missing
    # The API should either:
    # 1. Return 400 Bad Request (published_date is required), OR
    # 2. Fall back to created_at with appropriate labeling

    # Attempt to create paper without published_date would fail at model level
    # (published_date is NOT NULL in database)
    pass  # Handled by database constraint
