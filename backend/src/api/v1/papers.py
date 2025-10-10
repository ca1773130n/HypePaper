"""Papers API routes (Extended SOTAPapers integration).

Endpoints:
- GET /api/v1/papers - List with extended filters
- GET /api/v1/papers/{id} - Get single paper with full metadata
- GET /api/v1/papers/{id}/citations - Get bidirectional citations
- GET /api/v1/papers/{id}/github - Get GitHub metrics and history
"""
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import Paper, PaperReference, GitHubMetrics, GitHubStarSnapshot, PaperTopicMatch
from ...services import PaperService
from .dependencies import get_db

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


# Response models
class PaperExtended(BaseModel):
    """Paper with extended metadata (list view)."""

    id: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    legacy_id: Optional[str] = None
    title: str
    authors: list[str]
    abstract: str
    published_date: str
    year: Optional[int] = None
    venue: Optional[str] = None

    # AI-extracted fields
    primary_task: Optional[str] = None
    secondary_task: Optional[str] = None
    tertiary_task: Optional[str] = None
    primary_method: Optional[str] = None
    secondary_method: Optional[str] = None
    tertiary_method: Optional[str] = None
    datasets_used: Optional[list[str]] = None
    metrics_used: Optional[list[str]] = None

    # Conference metadata
    paper_type: Optional[str] = None
    session_type: Optional[str] = None
    accept_status: Optional[str] = None

    # URLs
    github_url: Optional[str] = None
    arxiv_url: Optional[str] = None
    pdf_url: Optional[str] = None
    youtube_url: Optional[str] = None
    project_page_url: Optional[str] = None

    # Metrics
    github_stars: Optional[int] = None
    github_weekly_hype: Optional[float] = None
    github_monthly_hype: Optional[float] = None
    citations_total: int = 0
    references_total: int = 0

    # Timestamps
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaperDetailed(PaperExtended):
    """Paper with detailed metadata including affiliations."""

    affiliations: Optional[dict] = None
    affiliations_country: Optional[dict] = None
    pages: Optional[dict] = None
    note: Optional[str] = None
    bibtex: Optional[str] = None
    comparisons: Optional[dict] = None
    limitations: Optional[str] = None
    has_pdf_content: bool = False
    llm_extractions_count: int = 0
    llm_extractions_verified_count: int = 0


class CitationRelationship(BaseModel):
    """Citation relationship between papers."""

    related_paper_id: str
    related_paper_title: str
    related_paper_authors: Optional[list[str]] = None
    related_paper_year: Optional[int] = None
    reference_text: Optional[str] = None
    match_score: Optional[float] = None
    match_method: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: str


class CitationsResponse(BaseModel):
    """Citations response with bidirectional relationships."""

    paper_id: str
    citations_in: list[CitationRelationship]
    citations_out: list[CitationRelationship]
    total_in: int
    total_out: int


class GitHubMetricsDetailed(BaseModel):
    """Detailed GitHub metrics with history."""

    paper_id: str
    repository_url: str
    repository_owner: str
    repository_name: str
    current_stats: dict
    hype_scores: dict
    repository_metadata: dict
    tracking_metadata: dict
    star_history: list[dict]


class PapersListResponse(BaseModel):
    """Paginated papers list response."""

    items: list[PaperExtended]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=PapersListResponse)
async def list_papers(
    # Pagination
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),

    # Sorting
    sort: str = Query(
        "published_date_desc",
        description="Sort option",
        regex="^(published_date_desc|published_date_asc|github_stars_desc|citations_desc|weekly_hype_desc|monthly_hype_desc)$"
    ),

    # Filters
    topic_id: Optional[str] = Query(None, description="Filter by topic ID"),
    primary_task: Optional[str] = Query(None, description="Filter by primary research task"),
    secondary_task: Optional[str] = Query(None, description="Filter by secondary research task"),
    method: Optional[str] = Query(None, description="Filter by method (primary/secondary/tertiary)"),
    datasets_used: Optional[str] = Query(None, description="Filter by dataset name (contains)"),
    metrics_used: Optional[str] = Query(None, description="Filter by evaluation metric"),
    min_github_stars: Optional[int] = Query(None, ge=0, description="Minimum GitHub stars"),
    min_citations: Optional[int] = Query(None, ge=0, description="Minimum citation count"),
    venue: Optional[str] = Query(None, description="Filter by venue/conference name"),
    year: Optional[int] = Query(None, ge=1900, le=2100, description="Filter by publication year"),
    year_min: Optional[int] = Query(None, description="Minimum publication year"),
    year_max: Optional[int] = Query(None, description="Maximum publication year"),
    has_github: Optional[bool] = Query(None, description="Filter papers with GitHub repositories"),
    paper_type: Optional[str] = Query(None, description="Filter by paper type"),
    accept_status: Optional[str] = Query(None, description="Filter by acceptance status"),
    search: Optional[str] = Query(None, description="Full-text search across title and abstract"),

    db: AsyncSession = Depends(get_db),
) -> PapersListResponse:
    """List papers with extended filtering and sorting.

    Supports filtering by AI-extracted metadata, GitHub metrics, and citations.
    """
    # Build base query with relationships
    query = select(Paper).options(
        selectinload(Paper.github_metrics),
        selectinload(Paper.citations_in),
        selectinload(Paper.citations_out),
    )

    # Apply filters
    filters = []

    # Topic filter (join with paper_topic_matches table)
    if topic_id:
        query = query.join(PaperTopicMatch, Paper.id == PaperTopicMatch.paper_id).where(
            PaperTopicMatch.topic_id == topic_id
        )

    if primary_task:
        filters.append(Paper.primary_task == primary_task)

    if secondary_task:
        filters.append(Paper.secondary_task == secondary_task)

    if method:
        filters.append(
            or_(
                Paper.primary_method == method,
                Paper.secondary_method == method,
                Paper.tertiary_method == method,
            )
        )

    if datasets_used:
        # JSONB containment query
        filters.append(Paper.datasets_used.contains([datasets_used]))

    if metrics_used:
        filters.append(Paper.metrics_used.contains([metrics_used]))

    if venue:
        filters.append(Paper.venue.ilike(f"%{venue}%"))

    if year:
        filters.append(Paper.year == year)

    if year_min:
        filters.append(Paper.year >= year_min)

    if year_max:
        filters.append(Paper.year <= year_max)

    if has_github is not None:
        if has_github:
            filters.append(Paper.github_url.isnot(None))
        else:
            filters.append(Paper.github_url.is_(None))

    if paper_type:
        filters.append(Paper.paper_type == paper_type)

    if accept_status:
        filters.append(Paper.accept_status == accept_status)

    if search:
        # Full-text search using PostgreSQL tsvector
        search_filter = or_(
            Paper.title.ilike(f"%{search}%"),
            Paper.abstract.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    # Apply sorting
    if sort == "published_date_desc":
        query = query.order_by(Paper.published_date.desc())
    elif sort == "published_date_asc":
        query = query.order_by(Paper.published_date.asc())
    elif sort == "github_stars_desc":
        # Join with GitHubMetrics for sorting
        query = (
            query.outerjoin(GitHubMetrics)
            .order_by(GitHubMetrics.current_stars.desc().nulls_last())
        )
    elif sort == "weekly_hype_desc":
        query = (
            query.outerjoin(GitHubMetrics)
            .order_by(GitHubMetrics.weekly_hype.desc().nulls_last())
        )
    elif sort == "monthly_hype_desc":
        query = (
            query.outerjoin(GitHubMetrics)
            .order_by(GitHubMetrics.monthly_hype.desc().nulls_last())
        )
    # citations_desc requires counting relationships - handled after fetch

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.limit(page_size).offset(offset)

    # Execute query
    result = await db.execute(query)
    papers = list(result.scalars().unique().all())

    # Filter by GitHub stars if specified (after loading relationships)
    if min_github_stars is not None:
        papers = [p for p in papers if p.github_metrics and p.github_metrics.current_stars >= min_github_stars]
        total = len(papers)

    # Filter by citations if specified
    if min_citations is not None:
        papers = [p for p in papers if len(p.citations_in) >= min_citations]
        total = len(papers)

    # Sort by citations if requested (after loading relationships)
    if sort == "citations_desc":
        papers.sort(key=lambda p: len(p.citations_in), reverse=True)

    # Build response
    items = []
    for paper in papers:
        github_stars = paper.github_metrics.current_stars if paper.github_metrics else None
        weekly_hype = paper.github_metrics.weekly_hype if paper.github_metrics else None
        monthly_hype = paper.github_metrics.monthly_hype if paper.github_metrics else None

        items.append(
            PaperExtended(
                id=str(paper.id),
                arxiv_id=paper.arxiv_id,
                doi=paper.doi,
                legacy_id=paper.legacy_id,
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                published_date=paper.published_date.isoformat(),
                year=paper.year,
                venue=paper.venue,
                primary_task=paper.primary_task,
                secondary_task=paper.secondary_task,
                tertiary_task=paper.tertiary_task,
                primary_method=paper.primary_method,
                secondary_method=paper.secondary_method,
                tertiary_method=paper.tertiary_method,
                datasets_used=paper.datasets_used,
                metrics_used=paper.metrics_used,
                paper_type=paper.paper_type,
                session_type=paper.session_type,
                accept_status=paper.accept_status,
                github_url=paper.github_url,
                arxiv_url=paper.arxiv_url,
                pdf_url=paper.pdf_url,
                youtube_url=paper.youtube_url,
                project_page_url=paper.project_page_url,
                github_stars=github_stars,
                github_weekly_hype=weekly_hype,
                github_monthly_hype=monthly_hype,
                citations_total=len(paper.citations_in),
                references_total=len(paper.citations_out),
                created_at=paper.created_at.isoformat(),
                updated_at=paper.updated_at.isoformat(),
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return PapersListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{paper_id}", response_model=PaperDetailed)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaperDetailed:
    """Get detailed paper information by UUID or ArXiv ID."""
    # Try to parse as UUID first
    try:
        paper_uuid = UUID(paper_id)
        query = select(Paper).where(Paper.id == paper_uuid)
    except ValueError:
        # Not a UUID, try as ArXiv ID
        query = select(Paper).where(Paper.arxiv_id == paper_id)

    query = query.options(
        selectinload(Paper.github_metrics),
        selectinload(Paper.citations_in),
        selectinload(Paper.citations_out),
        selectinload(Paper.pdf_content),
        selectinload(Paper.llm_extractions),
    )

    result = await db.execute(query)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Calculate metrics
    github_stars = paper.github_metrics.current_stars if paper.github_metrics else None
    weekly_hype = paper.github_metrics.weekly_hype if paper.github_metrics else None
    monthly_hype = paper.github_metrics.monthly_hype if paper.github_metrics else None

    has_pdf = paper.pdf_content is not None
    llm_count = len(paper.llm_extractions)
    llm_verified = len([e for e in paper.llm_extractions if e.verified_at is not None])

    return PaperDetailed(
        id=str(paper.id),
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        legacy_id=paper.legacy_id,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        published_date=paper.published_date.isoformat(),
        year=paper.year,
        venue=paper.venue,
        primary_task=paper.primary_task,
        secondary_task=paper.secondary_task,
        tertiary_task=paper.tertiary_task,
        primary_method=paper.primary_method,
        secondary_method=paper.secondary_method,
        tertiary_method=paper.tertiary_method,
        datasets_used=paper.datasets_used,
        metrics_used=paper.metrics_used,
        paper_type=paper.paper_type,
        session_type=paper.session_type,
        accept_status=paper.accept_status,
        github_url=paper.github_url,
        arxiv_url=paper.arxiv_url,
        pdf_url=paper.pdf_url,
        youtube_url=paper.youtube_url,
        project_page_url=paper.project_page_url,
        github_stars=github_stars,
        github_weekly_hype=weekly_hype,
        github_monthly_hype=monthly_hype,
        citations_total=len(paper.citations_in),
        references_total=len(paper.citations_out),
        created_at=paper.created_at.isoformat(),
        updated_at=paper.updated_at.isoformat(),
        affiliations=paper.affiliations,
        affiliations_country=paper.affiliations_country,
        pages=paper.pages,
        note=paper.note,
        bibtex=paper.bibtex,
        comparisons=paper.comparisons,
        limitations=paper.limitations,
        has_pdf_content=has_pdf,
        llm_extractions_count=llm_count,
        llm_extractions_verified_count=llm_verified,
    )


@router.get("/{paper_id}/citations", response_model=CitationsResponse)
async def get_paper_citations(
    paper_id: str,
    direction: str = Query("both", regex="^(in|out|both)$", description="Citation direction"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CitationsResponse:
    """Get citation relationships for a paper (bidirectional).

    Returns papers citing this paper (in) and papers cited by this paper (out).
    """
    # Get paper
    try:
        paper_uuid = UUID(paper_id)
        query = select(Paper).where(Paper.id == paper_uuid)
    except ValueError:
        query = select(Paper).where(Paper.arxiv_id == paper_id)

    result = await db.execute(query)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get citations
    citations_in = []
    citations_out = []

    if direction in ["in", "both"]:
        # Papers citing this paper
        query_in = (
            select(PaperReference)
            .where(PaperReference.reference_id == paper.id)
            .options(selectinload(PaperReference.paper))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        result_in = await db.execute(query_in)
        refs_in = list(result_in.scalars().all())

        for ref in refs_in:
            citing_paper = ref.paper
            citations_in.append(
                CitationRelationship(
                    related_paper_id=str(citing_paper.id),
                    related_paper_title=citing_paper.title,
                    related_paper_authors=citing_paper.authors,
                    related_paper_year=citing_paper.year,
                    reference_text=ref.reference_text,
                    match_score=ref.match_score,
                    match_method=ref.match_method,
                    verified_at=ref.verified_at.isoformat() if ref.verified_at else None,
                    created_at=ref.created_at.isoformat(),
                )
            )

    if direction in ["out", "both"]:
        # Papers cited by this paper
        query_out = (
            select(PaperReference)
            .where(PaperReference.paper_id == paper.id)
            .options(selectinload(PaperReference.referenced_paper))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        result_out = await db.execute(query_out)
        refs_out = list(result_out.scalars().all())

        for ref in refs_out:
            cited_paper = ref.referenced_paper
            citations_out.append(
                CitationRelationship(
                    related_paper_id=str(cited_paper.id),
                    related_paper_title=cited_paper.title,
                    related_paper_authors=cited_paper.authors,
                    related_paper_year=cited_paper.year,
                    reference_text=ref.reference_text,
                    match_score=ref.match_score,
                    match_method=ref.match_method,
                    verified_at=ref.verified_at.isoformat() if ref.verified_at else None,
                    created_at=ref.created_at.isoformat(),
                )
            )

    # Get totals
    count_in_query = select(func.count()).where(PaperReference.reference_id == paper.id)
    count_out_query = select(func.count()).where(PaperReference.paper_id == paper.id)

    total_in_result = await db.execute(count_in_query)
    total_out_result = await db.execute(count_out_query)

    total_in = total_in_result.scalar() or 0
    total_out = total_out_result.scalar() or 0

    return CitationsResponse(
        paper_id=str(paper.id),
        citations_in=citations_in,
        citations_out=citations_out,
        total_in=total_in,
        total_out=total_out,
    )


@router.get("/{paper_id}/github", response_model=GitHubMetricsDetailed)
async def get_paper_github(
    paper_id: str,
    history_days: int = Query(90, ge=1, le=365, description="Days of star history to return"),
    db: AsyncSession = Depends(get_db),
) -> GitHubMetricsDetailed:
    """Get GitHub repository metrics and star tracking history."""
    # Get paper with GitHub metrics
    try:
        paper_uuid = UUID(paper_id)
        query = select(Paper).where(Paper.id == paper_uuid)
    except ValueError:
        query = select(Paper).where(Paper.arxiv_id == paper_id)

    query = query.options(selectinload(Paper.github_metrics))
    result = await db.execute(query)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.github_metrics:
        raise HTTPException(
            status_code=404,
            detail="No GitHub repository associated with this paper"
        )

    metrics = paper.github_metrics

    # Get star history
    cutoff_date = date.today() - timedelta(days=history_days)
    history_query = (
        select(GitHubStarSnapshot)
        .where(
            and_(
                GitHubStarSnapshot.paper_id == paper.id,
                GitHubStarSnapshot.snapshot_date >= cutoff_date,
            )
        )
        .order_by(GitHubStarSnapshot.snapshot_date.desc())
    )
    history_result = await db.execute(history_query)
    snapshots = list(history_result.scalars().all())

    star_history = [
        {
            "date": snap.snapshot_date.isoformat(),
            "stars": snap.star_count,
            "forks": snap.fork_count,
            "watchers": snap.watcher_count,
            "stars_gained_since_yesterday": snap.stars_gained_since_yesterday,
        }
        for snap in snapshots
    ]

    return GitHubMetricsDetailed(
        paper_id=str(paper.id),
        repository_url=metrics.repository_url,
        repository_owner=metrics.repository_owner,
        repository_name=metrics.repository_name,
        current_stats={
            "stars": metrics.current_stars,
            "forks": metrics.current_forks,
            "watchers": metrics.current_watchers,
            "last_updated": metrics.last_tracked_at.isoformat(),
        },
        hype_scores={
            "average": metrics.average_hype,
            "weekly": metrics.weekly_hype,
            "monthly": metrics.monthly_hype,
        },
        repository_metadata={
            "primary_language": metrics.primary_language,
            "description": metrics.repository_description,
            "created_at": metrics.repository_created_at.isoformat() if metrics.repository_created_at else None,
            "updated_at": metrics.repository_updated_at.isoformat() if metrics.repository_updated_at else None,
        },
        tracking_metadata={
            "start_date": metrics.tracking_start_date.isoformat(),
            "last_tracked_at": metrics.last_tracked_at.isoformat(),
            "enabled": metrics.tracking_enabled,
        },
        star_history=star_history,
    )
