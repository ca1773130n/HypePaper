"""Enhanced paper endpoints with star history, hype scores, and PDF download."""
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import Paper, PaperReference, GitHubStarSnapshot, CitationSnapshot
from ...services.pdf_service import PDFService

router = APIRouter(prefix="/papers", tags=["Papers Enhanced"])

# Simple in-memory cache for hype scores (1 hour TTL)
hype_cache: Dict[str, Dict] = {}
cache_ttl = 3600  # 1 hour in seconds


class StarHistoryPoint(BaseModel):
    """Star history data point."""
    date: str
    stars: int
    citations: int = 0


class CitationHistoryPoint(BaseModel):
    """Citation history data point."""
    date: str
    citation_count: int


class HypeScoresResponse(BaseModel):
    """Hype scores breakdown."""
    average_hype: float
    weekly_hype: float
    monthly_hype: float
    formula_explanation: str


class ReferenceNode(BaseModel):
    """Citation graph node."""
    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    relationship: str  # "cites" or "cited_by"


class MetricPoint(BaseModel):
    """Metric snapshot data point."""
    snapshot_date: str
    citation_count: Optional[int] = None
    github_stars: Optional[int] = None
    vote_count: Optional[int] = None
    hype_score: Optional[float] = None


@router.get("/{paper_id}/metrics", response_model=List[MetricPoint])
async def get_metrics(
    paper_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get metrics history for a paper."""
    from datetime import datetime, timedelta
    from ...models import MetricSnapshot

    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get metric snapshots
    since_date = datetime.utcnow() - timedelta(days=days)

    snapshots_result = await db.execute(
        select(MetricSnapshot)
        .where(
            MetricSnapshot.paper_id == paper_id,
            MetricSnapshot.snapshot_date >= since_date
        )
        .order_by(MetricSnapshot.snapshot_date)
    )
    snapshots = snapshots_result.scalars().all()

    return [
        MetricPoint(
            snapshot_date=snap.snapshot_date.isoformat(),
            citation_count=snap.citation_count,
            github_stars=snap.github_stars,
            vote_count=snap.vote_count,
            hype_score=snap.hype_score
        )
        for snap in snapshots
    ]


@router.get("/{paper_id}/star-history", response_model=List[StarHistoryPoint])
async def get_star_history(
    paper_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get star history for a paper."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get star snapshots
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=days)

    snapshots_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= since_date
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    snapshots = snapshots_result.scalars().all()

    return [
        StarHistoryPoint(
            date=snap.snapshot_date.isoformat(),
            stars=snap.star_count,
            citations=paper.citations or 0
        )
        for snap in snapshots
    ]


@router.get("/{paper_id}/hype-scores", response_model=HypeScoresResponse)
async def get_hype_scores(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Calculate and return hype scores (cached for 1 hour)."""
    from datetime import date

    # Check cache first
    cache_key = str(paper_id)
    now = datetime.utcnow()
    if cache_key in hype_cache:
        cached_entry = hype_cache[cache_key]
        if (now - cached_entry['timestamp']).total_seconds() < cache_ttl:
            return cached_entry['data']

    # Single optimized query to get paper and all star snapshots we need
    paper_result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = paper_result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get all star snapshots for the last 30 days in one query (covers weekly and monthly)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    all_snaps_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= thirty_days_ago
        )
        .order_by(GitHubStarSnapshot.snapshot_date.desc())
    )
    all_snaps = list(all_snaps_result.scalars().all())

    # Get current stars (latest snapshot)
    stars = all_snaps[0].star_count if all_snaps else 0

    # Calculate age in days
    if paper.published_date:
        if isinstance(paper.published_date, date) and not isinstance(paper.published_date, datetime):
            pub_datetime = datetime.combine(paper.published_date, datetime.min.time())
        else:
            pub_datetime = paper.published_date
        age_days = (datetime.utcnow() - pub_datetime).days
    else:
        age_days = 1
    age_days = max(age_days, 1)

    # SOTAPapers formula: (citations * 100 + stars) / age_days
    citations = paper.citation_count or 0
    average_hype = (citations * 100 + stars) / age_days

    # Filter snapshots for weekly and monthly calculations
    weekly_snaps = [snap for snap in all_snaps if snap.snapshot_date >= seven_days_ago]
    monthly_snaps = all_snaps  # Already filtered to 30 days

    # Calculate weekly hype (last 7 days growth)
    weekly_hype = 0.0
    if len(weekly_snaps) >= 2:
        # Sort by date (oldest first) for growth calculation
        weekly_snaps.sort(key=lambda x: x.snapshot_date)
        star_growth = weekly_snaps[-1].star_count - weekly_snaps[0].star_count
        weekly_hype = star_growth / 7

    # Calculate monthly hype (last 30 days growth)
    monthly_hype = 0.0
    if len(monthly_snaps) >= 2:
        # Sort by date (oldest first) for growth calculation
        monthly_snaps.sort(key=lambda x: x.snapshot_date)
        star_growth = monthly_snaps[-1].star_count - monthly_snaps[0].star_count
        monthly_hype = star_growth / 30

    response = HypeScoresResponse(
        average_hype=round(average_hype, 2),
        weekly_hype=round(weekly_hype, 2),
        monthly_hype=round(monthly_hype, 2),
        formula_explanation=f"Average: (citations×100 + stars) / age_days = ({citations}×100 + {stars}) / {age_days}"
    )

    # Cache the result
    hype_cache[cache_key] = {
        'data': response,
        'timestamp': now
    }

    return response


@router.get("/{paper_id}/references", response_model=List[ReferenceNode])
async def get_references(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get citation graph (papers this cites + papers citing this)."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    nodes = []

    # Papers this paper cites (references)
    refs_result = await db.execute(
        select(PaperReference, Paper)
        .join(Paper, PaperReference.target_paper_id == Paper.id)
        .where(PaperReference.source_paper_id == paper_id)
    )
    for ref, cited_paper in refs_result:
        nodes.append(ReferenceNode(
            paper_id=str(cited_paper.id),
            title=cited_paper.title,
            authors=[cited_paper.authors] if isinstance(cited_paper.authors, str) else cited_paper.authors or [],
            year=cited_paper.published_date.year if cited_paper.published_date else None,
            relationship="cites"
        ))

    # Papers citing this paper
    citing_result = await db.execute(
        select(PaperReference, Paper)
        .join(Paper, PaperReference.source_paper_id == Paper.id)
        .where(PaperReference.target_paper_id == paper_id)
    )
    for ref, citing_paper in citing_result:
        nodes.append(ReferenceNode(
            paper_id=str(citing_paper.id),
            title=citing_paper.title,
            authors=[citing_paper.authors] if isinstance(citing_paper.authors, str) else citing_paper.authors or [],
            year=citing_paper.published_date.year if citing_paper.published_date else None,
            relationship="cited_by"
        ))

    return nodes


@router.get("/{paper_id}/citation-history", response_model=List[CitationHistoryPoint])
async def get_citation_history(
    paper_id: UUID,
    days: int = 365,
    db: AsyncSession = Depends(get_db)
):
    """Get citation history for a paper."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get citation snapshots
    from datetime import datetime, timedelta
    since_date = datetime.utcnow().date() - timedelta(days=days)

    snapshots_result = await db.execute(
        select(CitationSnapshot)
        .where(
            CitationSnapshot.paper_id == paper_id,
            CitationSnapshot.snapshot_date >= since_date
        )
        .order_by(CitationSnapshot.snapshot_date)
    )
    snapshots = snapshots_result.scalars().all()

    return [
        CitationHistoryPoint(
            date=snap.snapshot_date.isoformat(),
            citation_count=snap.citation_count
        )
        for snap in snapshots
    ]


@router.get("/{paper_id}/download-pdf")
async def download_pdf(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Download PDF file (downloads from source if not cached locally)."""
    pdf_service = PDFService(db)

    try:
        # This will download if needed
        pdf_path = await pdf_service.download_pdf(paper_id)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{paper_id}.pdf"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF download failed: {str(e)}")
