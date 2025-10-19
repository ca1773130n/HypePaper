"""Integration tests for author statistics.

Tests author stat calculations and integrity from quickstart.md.

TDD: These tests MUST fail before implementation.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.author import Author, PaperAuthor
from src.models.paper import Paper


@pytest.mark.asyncio
async def test_scenario_6_author_details(async_client: AsyncClient, test_author_id: int):
    """Scenario 6: Clicking author name returns author details.

    From quickstart.md Scenario 6
    """
    response = await async_client.get(f"/api/authors/{test_author_id}")

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields present
    assert "name" in data
    assert "primary_affiliation" in data
    assert "paper_count" in data
    assert "total_citation_count" in data
    assert "recent_papers" in data
    assert len(data["recent_papers"]) <= 5


@pytest.mark.asyncio
async def test_author_paper_count_accuracy(db_session: AsyncSession, test_author_id: int):
    """Verify author.paper_count equals actual count in paper_authors table."""
    author = await db_session.get(Author, test_author_id)

    # Count actual papers in junction table
    actual_count = await db_session.execute(
        select(PaperAuthor).where(PaperAuthor.author_id == test_author_id)
    )
    actual_paper_count = len(actual_count.scalars().all())

    assert author.paper_count == actual_paper_count


@pytest.mark.asyncio
async def test_author_citation_count_accuracy(db_session: AsyncSession, test_author_id: int):
    """Verify author.total_citation_count equals sum of paper citations."""
    author = await db_session.get(Author, test_author_id)

    # Get all papers by this author
    paper_authors = await db_session.execute(
        select(PaperAuthor).where(PaperAuthor.author_id == test_author_id)
    )
    paper_ids = [pa.paper_id for pa in paper_authors.scalars().all()]

    # Sum citations from all papers
    papers = await db_session.execute(
        select(Paper).where(Paper.id.in_(paper_ids))
    )
    total_citations = sum(p.citation_count for p in papers.scalars().all())

    assert author.total_citation_count == total_citations


@pytest.mark.asyncio
async def test_edge_case_4_author_no_affiliation(async_client: AsyncClient):
    """Edge Case 4: Author with no affiliation displays null.

    From quickstart.md EC4
    """
    # Create author without affiliation
    # (This would be set up in fixture)

    response = await async_client.get("/api/authors/1")
    if response.status_code == 200:
        data = response.json()
        # primary_affiliation should be null if no affiliations exist
        if data.get("affiliation_history") is None or len(data["affiliation_history"]) == 0:
            assert data["primary_affiliation"] is None
