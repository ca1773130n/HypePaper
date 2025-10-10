"""Admin endpoints for MVP testing interface."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import AdminTaskLog, Paper
from ...jobs.celery_app import celery_app
from ...api.dependencies import get_current_user_required

router = APIRouter(prefix="/admin", tags=["Admin"])


class CrawlArxivRequest(BaseModel):
    """Request to crawl ArXiv papers."""
    query: str
    limit: int = 100


class CrawlConferenceRequest(BaseModel):
    """Request to crawl conference papers."""
    conference_name: str
    conference_url: Optional[str] = None
    conference_year: Optional[int] = None


class TaskResponse(BaseModel):
    """Task execution response."""
    task_id: str
    status: str
    message: str


class TaskLogResponse(BaseModel):
    """Admin task log response."""
    id: str
    task_type: str
    task_params: Optional[dict]
    status: str
    result: Optional[dict]
    error: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/crawl/arxiv", response_model=TaskResponse)
async def trigger_arxiv_crawl(
    request: CrawlArxivRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger ArXiv paper crawling."""
    # Create task log
    task_log = AdminTaskLog(
        task_type="crawl_arxiv",
        task_params={"query": request.query, "limit": request.limit},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    # Enqueue Celery task
    celery_task = celery_app.send_task(
        "paper_crawler.crawl_arxiv",
        args=[request.query, request.limit]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"ArXiv crawl started for query: {request.query}"
    )


@router.post("/crawl/conference", response_model=TaskResponse)
async def trigger_conference_crawl(
    request: CrawlConferenceRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger conference paper crawling."""
    task_log = AdminTaskLog(
        task_type="crawl_conference",
        task_params={
            "conference_name": request.conference_name,
            "conference_url": request.conference_url,
            "conference_year": request.conference_year
        },
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "paper_crawler.crawl_conference",
        kwargs={
            "conference_name": request.conference_name,
            "conference_url": request.conference_url,
            "conference_year": request.conference_year
        }
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"Conference crawl started: {request.conference_name}"
    )


@router.post("/enrich/pdf/{paper_id}", response_model=TaskResponse)
async def trigger_pdf_enrichment(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger PDF enrichment for a specific paper."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="enrich_pdf",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "pdf_enrichment.enrich_paper",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"PDF enrichment started for paper {paper_id}"
    )


@router.post("/match/github/{paper_id}", response_model=TaskResponse)
async def trigger_github_matching(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger GitHub repository matching for a paper."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="match_github",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "github_matcher.match_repository",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"GitHub matching started for paper {paper_id}"
    )


@router.post("/extract/references/{paper_id}", response_model=TaskResponse)
async def trigger_reference_extraction(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger reference extraction from paper PDF."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="extract_references",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "reference_extractor.extract_references",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"Reference extraction started for paper {paper_id}"
    )


@router.get("/tasks", response_model=List[TaskLogResponse])
async def list_admin_tasks(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """List recent admin tasks."""
    result = await db.execute(
        select(AdminTaskLog)
        .order_by(desc(AdminTaskLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    tasks = result.scalars().all()

    return [
        TaskLogResponse(
            id=str(task.id),
            task_type=task.task_type,
            task_params=task.task_params,
            status=task.status,
            result=task.result,
            error=task.error,
            created_at=task.created_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskLogResponse)
async def get_task_details(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Get specific task details."""
    result = await db.execute(select(AdminTaskLog).where(AdminTaskLog.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskLogResponse(
        id=str(task.id),
        task_type=task.task_type,
        task_params=task.task_params,
        status=task.status,
        result=task.result,
        error=task.error,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )
