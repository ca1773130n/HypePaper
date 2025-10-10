"""Papers API routes.

Endpoints for querying research papers with filtering, sorting, and metrics.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services import HypeScoreService, MetricService, PaperService
from .cache import cache, cache_papers_list

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


# Response models
class PaperListItem(BaseModel):
    """Paper list item schema (summary)."""

    id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: str
    venue: Optional[str] = None
    github_url: Optional[str] = None
    hype_score: float
    trend_label: str

    class Config:
        """Pydantic config."""
        from_attributes = True


class PapersListResponse(BaseModel):
    """Papers list response schema."""

    papers: list[PaperListItem]
    total: int
    limit: int
    offset: int


class PaperDetailResponse(BaseModel):
    """Paper detail response schema."""

    id: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    title: str
    authors: list[str]
    abstract: str
    published_date: str
    venue: Optional[str] = None
    github_url: Optional[str] = None
    arxiv_url: Optional[str] = None
    pdf_url: Optional[str] = None
    hype_score: float
    star_growth_7d: float
    citation_growth_30d: float
    current_stars: int
    trend_label: str
    created_at: str

    class Config:
        """Pydantic config."""
        from_attributes = True


class MetricSnapshot(BaseModel):
    """Metric snapshot schema."""

    snapshot_date: str
    github_stars: Optional[int] = None
    citation_count: Optional[int] = None


class PaperMetricsResponse(BaseModel):
    """Paper metrics history response."""

    paper_id: str
    metrics: list[MetricSnapshot]


# Import database session dependency
from ..database import get_db


@router.get("", response_model=PapersListResponse)
async def get_papers(
    topic_id: Optional[UUID] = Query(None, description="Filter by topic ID"),
    sort: str = Query("recency", description="Sort option: hype_score, recency, stars"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> PapersListResponse:
    """Get papers with filtering and sorting.

    Args:
        topic_id: Filter by topic (optional)
        sort: Sort option (hype_score, recency, stars)
        limit: Maximum results
        offset: Pagination offset
        db: Database session

    Returns:
        PapersListResponse with papers array and pagination info (cached for 1 hour)

    Raises:
        HTTPException: 400/422 if invalid sort parameter
    """
    # Validate sort parameter
    valid_sorts = ["hype_score", "recency", "stars"]
    if sort not in valid_sorts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort parameter. Must be one of: {', '.join(valid_sorts)}",
        )

    # Check cache first (1-hour TTL for hype scores)
    cache_key = cache_papers_list(
        topic_id=str(topic_id) if topic_id else None,
        sort_by=sort,
        limit=limit,
    )
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    paper_service = PaperService(db)
    hype_score_service = HypeScoreService(db)

    papers, total = await paper_service.get_papers(
        topic_id=topic_id,
        sort_by=sort,
        limit=limit,
        offset=offset,
    )

    # Calculate hype scores for each paper
    paper_items = []
    for paper in papers:
        hype_data = await hype_score_service.calculate_hype_score(paper)

        paper_items.append(
            PaperListItem(
                id=str(paper.id),
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                published_date=paper.published_date.isoformat(),
                venue=paper.venue,
                github_url=paper.github_url,
                hype_score=hype_data["hype_score"],
                trend_label=hype_data["trend_label"],
            )
        )

    response = PapersListResponse(
        papers=paper_items,
        total=total,
        limit=limit,
        offset=offset,
    )

    # Cache response for 1 hour (3600 seconds)
    cache.set(cache_key, response, ttl_seconds=3600)

    return response


@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper_by_id(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PaperDetailResponse:
    """Get paper details by ID.

    Args:
        paper_id: Paper UUID
        db: Database session

    Returns:
        PaperDetailResponse with full paper details

    Raises:
        HTTPException: 404 if paper not found
    """
    paper_service = PaperService(db)
    hype_score_service = HypeScoreService(db)

    paper = await paper_service.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    hype_data = await hype_score_service.calculate_hype_score(paper)

    return PaperDetailResponse(
        id=str(paper.id),
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        published_date=paper.published_date.isoformat(),
        venue=paper.venue,
        github_url=paper.github_url,
        arxiv_url=paper.arxiv_url,
        pdf_url=paper.pdf_url,
        hype_score=hype_data["hype_score"],
        star_growth_7d=hype_data["star_growth_7d"],
        citation_growth_30d=hype_data["citation_growth_30d"],
        current_stars=hype_data["current_stars"],
        trend_label=hype_data["trend_label"],
        created_at=paper.created_at.isoformat(),
    )


@router.get("/{paper_id}/metrics", response_model=PaperMetricsResponse)
async def get_paper_metrics(
    paper_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Days of history"),
    db: AsyncSession = Depends(get_db),
) -> PaperMetricsResponse:
    """Get metric history for a paper.

    Args:
        paper_id: Paper UUID
        days: Number of days of history
        db: Database session

    Returns:
        PaperMetricsResponse with metrics array

    Raises:
        HTTPException: 404 if paper not found
    """
    paper_service = PaperService(db)
    metric_service = MetricService(db)

    # Check if paper exists
    paper = await paper_service.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get metrics
    metrics = await metric_service.get_metrics(paper_id, days=days)

    return PaperMetricsResponse(
        paper_id=str(paper_id),
        metrics=[
            MetricSnapshot(
                snapshot_date=m.snapshot_date.isoformat(),
                github_stars=m.github_stars,
                citation_count=m.citation_count,
            )
            for m in metrics
        ],
    )
