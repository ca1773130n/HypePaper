"""Enhanced paper endpoints with star history, hype scores, and PDF download."""
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import Paper, PaperReference, GitHubStarSnapshot, CitationSnapshot
from ...services.pdf_service import PDFService

router = APIRouter(prefix="/papers", tags=["Papers Enhanced"])


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
    """Calculate and return hype scores."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get latest star count
    latest_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(GitHubStarSnapshot.paper_id == paper_id)
        .order_by(GitHubStarSnapshot.snapshot_date.desc())
        .limit(1)
    )
    latest_snap = latest_snap_result.scalar_one_or_none()
    stars = latest_snap.star_count if latest_snap else 0

    # Calculate age in days
    from datetime import datetime, date
    if paper.published_date:
        # Convert date to datetime if needed
        if isinstance(paper.published_date, date) and not isinstance(paper.published_date, datetime):
            pub_datetime = datetime.combine(paper.published_date, datetime.min.time())
        else:
            pub_datetime = paper.published_date
        age_days = (datetime.utcnow() - pub_datetime).days
    else:
        age_days = 1
    age_days = max(age_days, 1)

    # SOTAPapers formula: (citations * 100 + stars) / age_days
    citations = paper.citations or 0
    average_hype = (citations * 100 + stars) / age_days

    # Weekly hype (last 7 days growth)
    weekly_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= datetime.utcnow() - timedelta(days=7)
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    weekly_snaps = weekly_snap_result.scalars().all()
    weekly_hype = 0.0
    if len(weekly_snaps) >= 2:
        star_growth = weekly_snaps[-1].star_count - weekly_snaps[0].star_count
        weekly_hype = star_growth / 7

    # Monthly hype (last 30 days growth)
    monthly_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= datetime.utcnow() - timedelta(days=30)
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    monthly_snaps = monthly_snap_result.scalars().all()
    monthly_hype = 0.0
    if len(monthly_snaps) >= 2:
        star_growth = monthly_snaps[-1].star_count - monthly_snaps[0].star_count
        monthly_hype = star_growth / 30

    return HypeScoresResponse(
        average_hype=round(average_hype, 2),
        weekly_hype=round(weekly_hype, 2),
        monthly_hype=round(monthly_hype, 2),
        formula_explanation=f"Average: (citations×100 + stars) / age_days = ({citations}×100 + {stars}) / {age_days}"
    )


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
