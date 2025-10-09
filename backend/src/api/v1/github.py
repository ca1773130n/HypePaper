"""GitHub API routes (Repository tracking and hype metrics).

Endpoints:
- GET /api/v1/github/metrics/{paper_id} - Time-series GitHub metrics
- GET /api/v1/github/trending - Trending papers by hype score
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import Paper, GitHubMetrics, GitHubStarSnapshot
from .dependencies import get_db

router = APIRouter(prefix="/api/v1/github", tags=["github"])


# Response models
class StarHistoryPoint(BaseModel):
    """Single point in star history."""

    date: str
    stars: int
    forks: Optional[int] = None
    watchers: Optional[int] = None
    delta: Optional[int] = None


class GitHubMetrics(BaseModel):
    """GitHub metrics response."""

    paper_id: str
    paper_title: str
    repository: dict
    current_stats: dict
    hype_scores: dict
    tracking: dict
    star_history: list[StarHistoryPoint]


class TrendingPaper(BaseModel):
    """Trending paper with GitHub metrics."""

    paper_id: str
    arxiv_id: Optional[str] = None
    title: str
    authors: list[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    primary_task: Optional[str] = None
    repository_url: str
    repository_name: str
    repository_owner: str
    primary_language: Optional[str] = None
    current_stars: int
    hype_score: float
    hype_metadata: Optional[dict] = None
    trending_rank: int
    citations_count: Optional[int] = None


class TrendingResponse(BaseModel):
    """Trending papers response."""

    papers: list[TrendingPaper]
    total: int
    page: int
    page_size: int
    period: str
    sort_by: str


@router.get("/metrics/{paper_id}", response_model=GitHubMetrics)
async def get_github_metrics(
    paper_id: str,
    history_days: int = Query(90, ge=1, le=365, description="Days of star history"),
    aggregate: str = Query(
        "daily",
        regex="^(daily|weekly|monthly)$",
        description="Aggregate history by period"
    ),
    db: AsyncSession = Depends(get_db),
) -> GitHubMetrics:
    """Get comprehensive GitHub metrics with time-series star history.

    Returns current repository stats, hype scores, and historical snapshots.
    """
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
        .order_by(GitHubStarSnapshot.snapshot_date.asc())
    )
    history_result = await db.execute(history_query)
    snapshots = list(history_result.scalars().all())

    # Aggregate if requested
    star_history = []

    if aggregate == "daily":
        # Return daily snapshots as-is
        for snap in snapshots:
            star_history.append(
                StarHistoryPoint(
                    date=snap.snapshot_date.isoformat(),
                    stars=snap.star_count,
                    forks=snap.fork_count,
                    watchers=snap.watcher_count,
                    delta=snap.stars_gained_since_yesterday,
                )
            )

    elif aggregate == "weekly":
        # Aggregate by week (Sunday to Saturday)
        current_week = []
        current_week_start = None

        for snap in snapshots:
            week_start = snap.snapshot_date - timedelta(days=snap.snapshot_date.weekday())

            if current_week_start is None:
                current_week_start = week_start

            if week_start != current_week_start:
                # New week, aggregate previous week
                if current_week:
                    first_snap = current_week[0]
                    last_snap = current_week[-1]
                    delta = last_snap.star_count - first_snap.star_count

                    star_history.append(
                        StarHistoryPoint(
                            date=current_week_start.isoformat(),
                            stars=last_snap.star_count,
                            forks=last_snap.fork_count,
                            watchers=last_snap.watcher_count,
                            delta=delta,
                        )
                    )

                current_week = [snap]
                current_week_start = week_start
            else:
                current_week.append(snap)

        # Add last week
        if current_week:
            first_snap = current_week[0]
            last_snap = current_week[-1]
            delta = last_snap.star_count - first_snap.star_count

            star_history.append(
                StarHistoryPoint(
                    date=current_week_start.isoformat(),
                    stars=last_snap.star_count,
                    forks=last_snap.fork_count,
                    watchers=last_snap.watcher_count,
                    delta=delta,
                )
            )

    elif aggregate == "monthly":
        # Aggregate by month
        current_month = []
        current_month_start = None

        for snap in snapshots:
            month_start = snap.snapshot_date.replace(day=1)

            if current_month_start is None:
                current_month_start = month_start

            if month_start != current_month_start:
                # New month, aggregate previous month
                if current_month:
                    first_snap = current_month[0]
                    last_snap = current_month[-1]
                    delta = last_snap.star_count - first_snap.star_count

                    star_history.append(
                        StarHistoryPoint(
                            date=current_month_start.isoformat(),
                            stars=last_snap.star_count,
                            forks=last_snap.fork_count,
                            watchers=last_snap.watcher_count,
                            delta=delta,
                        )
                    )

                current_month = [snap]
                current_month_start = month_start
            else:
                current_month.append(snap)

        # Add last month
        if current_month:
            first_snap = current_month[0]
            last_snap = current_month[-1]
            delta = last_snap.star_count - first_snap.star_count

            star_history.append(
                StarHistoryPoint(
                    date=current_month_start.isoformat(),
                    stars=last_snap.star_count,
                    forks=last_snap.fork_count,
                    watchers=last_snap.watcher_count,
                    delta=delta,
                )
            )

    return GitHubMetrics(
        paper_id=str(paper.id),
        paper_title=paper.title,
        repository={
            "url": metrics.repository_url,
            "owner": metrics.repository_owner,
            "name": metrics.repository_name,
            "description": metrics.repository_description,
            "primary_language": metrics.primary_language,
            "created_at": metrics.repository_created_at.isoformat() if metrics.repository_created_at else None,
            "updated_at": metrics.repository_updated_at.isoformat() if metrics.repository_updated_at else None,
        },
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
        tracking={
            "start_date": metrics.tracking_start_date.isoformat(),
            "last_tracked": metrics.last_tracked_at.isoformat(),
            "total_snapshots": len(snapshots),
            "enabled": metrics.tracking_enabled,
        },
        star_history=star_history,
    )


@router.get("/trending", response_model=TrendingResponse)
async def get_trending_papers(
    sort_by: str = Query(
        "weekly_hype",
        regex="^(weekly_hype|monthly_hype|average_hype|total_stars)$",
        description="Hype metric to sort by"
    ),
    period: str = Query(
        "week",
        regex="^(day|week|month|quarter|year|all_time)$",
        description="Time period for trending"
    ),
    min_stars: int = Query(100, ge=0, description="Minimum current stars"),
    primary_task: Optional[str] = Query(None, description="Filter by research task"),
    venue: Optional[str] = Query(None, description="Filter by venue/conference"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    language: Optional[str] = Query(None, description="Filter by primary language"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TrendingResponse:
    """Get trending papers sorted by GitHub hype scores.

    Returns papers with rapidly growing repositories, sorted by specified metric.
    """
    # Build base query
    query = (
        select(Paper)
        .join(GitHubMetrics, GitHubMetrics.paper_id == Paper.id)
        .where(GitHubMetrics.current_stars >= min_stars)
        .options(
            selectinload(Paper.github_metrics),
            selectinload(Paper.citations_in),
        )
    )

    # Apply filters
    filters = []

    if primary_task:
        filters.append(Paper.primary_task == primary_task)

    if venue:
        filters.append(Paper.venue.ilike(f"%{venue}%"))

    if year:
        filters.append(Paper.year == year)

    if language:
        filters.append(GitHubMetrics.primary_language == language)

    # Apply period filter (based on tracking date)
    if period == "day":
        cutoff = date.today() - timedelta(days=1)
    elif period == "week":
        cutoff = date.today() - timedelta(days=7)
    elif period == "month":
        cutoff = date.today() - timedelta(days=30)
    elif period == "quarter":
        cutoff = date.today() - timedelta(days=90)
    elif period == "year":
        cutoff = date.today() - timedelta(days=365)
    else:  # all_time
        cutoff = None

    if cutoff:
        filters.append(GitHubMetrics.tracking_start_date <= cutoff)

    if filters:
        query = query.where(and_(*filters))

    # Apply sorting
    if sort_by == "weekly_hype":
        query = query.order_by(GitHubMetrics.weekly_hype.desc().nulls_last())
    elif sort_by == "monthly_hype":
        query = query.order_by(GitHubMetrics.monthly_hype.desc().nulls_last())
    elif sort_by == "average_hype":
        query = query.order_by(GitHubMetrics.average_hype.desc().nulls_last())
    elif sort_by == "total_stars":
        query = query.order_by(GitHubMetrics.current_stars.desc())

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

    # Build response
    trending_papers = []
    for idx, paper in enumerate(papers, start=1):
        metrics = paper.github_metrics

        # Determine hype score based on sort_by
        if sort_by == "weekly_hype":
            hype_score = metrics.weekly_hype or 0.0
        elif sort_by == "monthly_hype":
            hype_score = metrics.monthly_hype or 0.0
        elif sort_by == "average_hype":
            hype_score = metrics.average_hype or 0.0
        else:  # total_stars
            hype_score = float(metrics.current_stars)

        trending_papers.append(
            TrendingPaper(
                paper_id=str(paper.id),
                arxiv_id=paper.arxiv_id,
                title=paper.title,
                authors=paper.authors,
                year=paper.year,
                venue=paper.venue,
                primary_task=paper.primary_task,
                repository_url=metrics.repository_url,
                repository_name=metrics.repository_name,
                repository_owner=metrics.repository_owner,
                primary_language=metrics.primary_language,
                current_stars=metrics.current_stars,
                hype_score=hype_score,
                hype_metadata={
                    "average_hype": metrics.average_hype,
                    "weekly_hype": metrics.weekly_hype,
                    "monthly_hype": metrics.monthly_hype,
                },
                trending_rank=offset + idx,
                citations_count=len(paper.citations_in),
            )
        )

    return TrendingResponse(
        papers=trending_papers,
        total=total,
        page=page,
        page_size=page_size,
        period=period,
        sort_by=sort_by,
    )
