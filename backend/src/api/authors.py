"""Author API endpoints.

Provides endpoints for retrieving author information and statistics.
"""
from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.author_service import AuthorService


router = APIRouter(prefix="/api/authors", tags=["authors"])


# Response models
class AuthorResponse(BaseModel):
    """Author information response."""
    id: int
    name: str
    affiliations: Optional[List[str]] = None
    paper_count: int
    total_citation_count: int
    email: Optional[str] = None
    website_url: Optional[str] = None
    created_at: date
    updated_at: date

    # Computed properties
    primary_affiliation: Optional[str] = None
    avg_citations_per_paper: float = 0.0

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_computed(cls, author):
        """Create response with computed properties."""
        data = {
            "id": author.id,
            "name": author.name,
            "affiliations": author.affiliations,
            "paper_count": author.paper_count,
            "total_citation_count": author.total_citation_count,
            "email": author.email,
            "website_url": author.website_url,
            "created_at": author.created_at,
            "updated_at": author.updated_at,
            "primary_affiliation": author.primary_affiliation,
            "avg_citations_per_paper": author.avg_citations_per_paper,
        }
        return cls(**data)


class AuthorListResponse(BaseModel):
    """List of authors response."""
    authors: List[AuthorResponse]
    total: int


@router.get(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Get author by ID"
)
async def get_author(
    author_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Get author details by ID.

    Returns author information including:
    - Name, affiliations, contact info
    - Paper count and total citations
    - Computed properties (primary affiliation, avg citations)

    Args:
        author_id: Author ID
        session: Database session

    Returns:
        AuthorResponse with full author details

    Raises:
        404: Author not found
    """
    author_service = AuthorService(session)
    author = await author_service.get_author_by_id(author_id, include_papers=False)

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author not found: {author_id}"
        )

    return AuthorResponse.from_orm_with_computed(author)


@router.get(
    "/",
    response_model=AuthorListResponse,
    summary="Search authors"
)
async def search_authors(
    q: Optional[str] = Query(None, description="Search query for author name"),
    affiliation: Optional[str] = Query(None, description="Filter by affiliation"),
    min_papers: Optional[int] = Query(None, ge=1, description="Minimum paper count"),
    min_citations: Optional[int] = Query(None, ge=1, description="Minimum total citations"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    session: AsyncSession = Depends(get_db)
):
    """Search and filter authors.

    Supports:
    - Full-text search by name (q parameter)
    - Filter by affiliation
    - Filter by minimum papers or citations
    - Ranked by paper_count or citation_count

    Args:
        q: Search query for author name
        affiliation: Filter by institution
        min_papers: Minimum paper count
        min_citations: Minimum citation count
        limit: Maximum results (1-100)
        session: Database session

    Returns:
        AuthorListResponse with matching authors
    """
    author_service = AuthorService(session)

    # Priority: affiliation > min_citations > min_papers > search query
    if affiliation:
        authors = await author_service.get_authors_by_affiliation(
            affiliation=affiliation,
            limit=limit
        )
    elif min_citations:
        authors = await author_service.get_highly_cited_authors(
            min_citations=min_citations,
            limit=limit
        )
    elif min_papers:
        authors = await author_service.get_prolific_authors(
            min_papers=min_papers,
            limit=limit
        )
    elif q:
        authors = await author_service.search_authors(
            query=q,
            limit=limit
        )
    else:
        # Default: return top authors by paper count
        authors = await author_service.get_prolific_authors(
            min_papers=1,
            limit=limit
        )

    author_responses = [
        AuthorResponse.from_orm_with_computed(author)
        for author in authors
    ]

    return AuthorListResponse(
        authors=author_responses,
        total=len(author_responses)
    )
