"""Authors API endpoints for Feature 003: Paper Enrichment."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database import get_db
from ...models import Author, Paper, PaperAuthor

router = APIRouter()


class AuthorResponse(BaseModel):
    """Response model for author information."""
    id: int
    name: str
    primary_affiliation: Optional[str] = None
    paper_count: Optional[int] = None
    total_citation_count: Optional[int] = None
    email: Optional[str] = None
    website_url: Optional[str] = None

    class Config:
        from_attributes = True


class AuthorPaper(BaseModel):
    """Paper information for author's recent papers."""
    id: UUID
    title: str
    published_date: Optional[str] = None
    citation_count: Optional[int] = None


@router.get("/search", response_model=List[AuthorResponse])
async def search_authors(
    q: str = Query(..., min_length=1, description="Search query for author name"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for authors by name.

    - **q**: Search query (required)
    - **limit**: Maximum number of results (default: 10)
    """
    # Search for authors by name (case-insensitive)
    query = (
        select(Author)
        .where(func.lower(Author.name).contains(func.lower(q)))
        .limit(limit)
    )

    result = await db.execute(query)
    authors = result.scalars().all()

    return [AuthorResponse.model_validate(author) for author in authors]


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific author.

    - **author_id**: Author ID
    """
    query = select(Author).where(Author.id == author_id)
    result = await db.execute(query)
    author = result.scalar_one_or_none()

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )

    return AuthorResponse.model_validate(author)


@router.get("/{author_id}/papers", response_model=List[AuthorPaper])
async def get_author_papers(
    author_id: int,
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("published_date", regex="^(published_date|citation_count)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get papers by a specific author.

    - **author_id**: Author ID
    - **limit**: Maximum number of results (default: 10)
    - **sort_by**: Sort by published_date or citation_count (default: published_date)
    """
    # Verify author exists
    author_query = select(Author).where(Author.id == author_id)
    author_result = await db.execute(author_query)
    author = author_result.scalar_one_or_none()

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )

    # Get papers by this author
    query = (
        select(Paper)
        .join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
        .where(PaperAuthor.author_id == author_id)
    )

    # Add sorting
    if sort_by == "published_date":
        query = query.order_by(desc(Paper.published_date))
    else:  # citation_count
        query = query.order_by(desc(Paper.citation_count))

    query = query.limit(limit)

    result = await db.execute(query)
    papers = result.scalars().all()

    return [
        AuthorPaper(
            id=paper.id,
            title=paper.title,
            published_date=paper.published_date.isoformat() if paper.published_date else None,
            citation_count=paper.citation_count
        )
        for paper in papers
    ]
