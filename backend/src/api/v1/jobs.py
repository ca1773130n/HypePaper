"""Jobs API routes (Background job management).

Endpoints:
- POST /api/v1/jobs/crawl - Trigger background crawl job
- GET /api/v1/jobs/{job_id} - Get job status and progress
- POST /api/v1/jobs/{job_id}/cancel - Cancel running job
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...jobs.celery_app import celery_app
from .dependencies import get_db

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# Request/Response models
class CrawlJobRequest(BaseModel):
    """Request to trigger a crawl job."""

    source: str = Field(..., description="Crawl source", pattern="^(arxiv|conference|citations)$")

    # ArXiv-specific
    arxiv_keywords: Optional[str] = None
    arxiv_category: Optional[str] = None
    arxiv_max_results: int = Field(default=100, ge=1, le=1000)

    # Conference-specific
    conference_name: Optional[str] = None
    conference_year: Optional[int] = None

    # Citation-specific
    seed_paper_ids: Optional[list[str]] = None
    citation_depth: int = Field(default=1, ge=1, le=3)

    # Common
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    enable_enrichment: bool = False


class EnrichJobRequest(BaseModel):
    """Request to trigger enrichment job."""

    paper_ids: Optional[list[str]] = None
    enrichment_tasks: list[str] = Field(
        default=[
            "download_pdf",
            "extract_text",
            "extract_tables",
            "extract_citations",
            "llm_extract_tasks",
            "llm_extract_methods",
            "llm_extract_datasets",
        ]
    )
    llm_provider: str = Field(default="llamacpp", pattern="^(openai|llamacpp)$")
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    force_reprocess: bool = False


class JobResponse(BaseModel):
    """Job creation response."""

    job_id: str
    job_type: str
    status: str
    created_at: str
    estimated_completion: Optional[str] = None
    metadata: Optional[dict] = None


class JobProgress(BaseModel):
    """Job progress metrics."""

    total: int
    completed: int
    failed: int
    percentage: float


class JobLog(BaseModel):
    """Job log entry."""

    timestamp: str
    level: str
    message: str


class JobStatus(BaseModel):
    """Detailed job status."""

    job_id: str
    job_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    progress: Optional[JobProgress] = None
    results: Optional[dict] = None
    error: Optional[str] = None
    logs: Optional[list[JobLog]] = None


class JobSummary(BaseModel):
    """Job summary for list view."""

    job_id: str
    job_type: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    progress_percentage: Optional[float] = None
    results_summary: Optional[str] = None


@router.post("/crawl", response_model=JobResponse, status_code=202)
async def trigger_crawl(
    request: CrawlJobRequest,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Trigger background paper crawling job.

    Sources:
    - arxiv: Crawl papers from ArXiv by keywords or category
    - conference: Crawl papers from conference proceedings
    - citations: Expand from seed papers via citation network

    Returns job ID for status monitoring.
    """
    # Validate source-specific parameters
    if request.source == "arxiv":
        if not request.arxiv_keywords and not request.arxiv_category:
            raise HTTPException(
                status_code=400,
                detail="Either arxiv_keywords or arxiv_category must be provided for ArXiv crawl"
            )

    elif request.source == "conference":
        if not request.conference_name or not request.conference_year:
            raise HTTPException(
                status_code=400,
                detail="Both conference_name and conference_year are required for conference crawl"
            )

    elif request.source == "citations":
        if not request.seed_paper_ids or len(request.seed_paper_ids) == 0:
            raise HTTPException(
                status_code=400,
                detail="seed_paper_ids must be provided for citation crawl"
            )

    # Generate job ID
    job_id = f"crawl-{request.source}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # Determine job type and parameters
    job_type = f"crawl_{request.source}"
    task_name = "jobs.paper_crawler.crawl_papers"

    # Build task kwargs based on source
    task_kwargs = {"source": request.source}

    if request.source == "arxiv":
        task_kwargs.update({
            "arxiv_keywords": request.arxiv_keywords,
            "arxiv_category": request.arxiv_category,
            "arxiv_max_results": request.arxiv_max_results,
        })
    elif request.source == "conference":
        task_kwargs.update({
            "conference_name": request.conference_name,
            "conference_year": request.conference_year,
        })
    else:  # citations
        task_kwargs.update({
            "seed_paper_ids": request.seed_paper_ids,
            "citation_depth": request.citation_depth,
        })

    # Queue Celery task
    try:
        task = celery_app.send_task(
            task_name,
            kwargs=task_kwargs,
            task_id=job_id,
            priority={"low": 3, "normal": 5, "high": 9}.get(request.priority, 5),
        )

        # Estimate completion time (rough estimate)
        if request.source == "arxiv":
            estimated_minutes = request.arxiv_max_results // 10
        elif request.source == "conference":
            estimated_minutes = 30
        else:  # citations
            estimated_minutes = len(request.seed_paper_ids or []) * 5 * request.citation_depth

        estimated_completion = datetime.utcnow().isoformat() + f"+00:00"  # Simplified

        return JobResponse(
            job_id=job_id,
            job_type=job_type,
            status="queued",
            created_at=datetime.utcnow().isoformat(),
            estimated_completion=estimated_completion,
            metadata={
                "source": request.source,
                "enable_enrichment": request.enable_enrichment,
                **task_kwargs,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue crawl job: {str(e)}"
        )


@router.post("/enrich", response_model=JobResponse, status_code=202)
async def trigger_enrich(
    request: EnrichJobRequest,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Trigger background metadata enrichment job.

    Enrichment tasks:
    - download_pdf: Download paper PDF
    - extract_text: Extract full text from PDF
    - extract_tables: Extract tables using GMFT
    - extract_citations: Parse bibliography
    - llm_extract_tasks: Extract research tasks via LLM
    - llm_extract_methods: Extract methods via LLM
    - llm_extract_datasets: Extract datasets via LLM

    Returns job ID for status monitoring.
    """
    # Generate job ID
    job_id = f"enrich-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # Queue Celery task
    try:
        task = celery_app.send_task(
            "jobs.metadata_enricher.enrich_paper",
            kwargs={
                "paper_ids": request.paper_ids,
                "enrichment_tasks": request.enrichment_tasks,
                "llm_provider": request.llm_provider,
                "force_reprocess": request.force_reprocess,
            },
            task_id=job_id,
            priority={"low": 3, "normal": 5, "high": 9}.get(request.priority, 5),
        )

        return JobResponse(
            job_id=job_id,
            job_type="enrich_metadata",
            status="queued",
            created_at=datetime.utcnow().isoformat(),
            metadata={
                "paper_ids": request.paper_ids,
                "enrichment_tasks": request.enrichment_tasks,
                "llm_provider": request.llm_provider,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue enrichment job: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobStatus:
    """Get detailed job status including progress and results.

    Status values:
    - queued: Job is waiting to be processed
    - processing: Job is currently running
    - completed: Job finished successfully
    - failed: Job encountered an error
    - cancelled: Job was cancelled by user
    """
    # Query Celery for task status
    try:
        task_result = celery_app.AsyncResult(job_id)

        # Map Celery states to our states
        status_map = {
            "PENDING": "queued",
            "STARTED": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "REVOKED": "cancelled",
        }

        status = status_map.get(task_result.state, "unknown")

        # Extract job type from job_id
        job_type_map = {
            "crawl-arxiv": "crawl_arxiv",
            "crawl-conference": "crawl_conference",
            "crawl-citations": "crawl_citations",
            "enrich": "enrich_metadata",
            "track": "track_github_stars",
        }

        job_type = "unknown"
        for prefix, type_name in job_type_map.items():
            if job_id.startswith(prefix):
                job_type = type_name
                break

        # Build response
        response = JobStatus(
            job_id=job_id,
            job_type=job_type,
            status=status,
            created_at=datetime.utcnow().isoformat(),  # Would get from task metadata
        )

        # Add task-specific information
        if task_result.state == "SUCCESS":
            result = task_result.result
            if isinstance(result, dict):
                response.results = result
                response.completed_at = datetime.utcnow().isoformat()

                # Calculate progress
                if "total" in result and "completed" in result:
                    total = result["total"]
                    completed = result["completed"]
                    failed = result.get("failed", 0)
                    response.progress = JobProgress(
                        total=total,
                        completed=completed,
                        failed=failed,
                        percentage=100.0,
                    )

        elif task_result.state == "STARTED":
            # Get progress from task metadata
            info = task_result.info
            if isinstance(info, dict):
                if "progress" in info:
                    prog = info["progress"]
                    response.progress = JobProgress(
                        total=prog.get("total", 0),
                        completed=prog.get("completed", 0),
                        failed=prog.get("failed", 0),
                        percentage=prog.get("percentage", 0.0),
                    )

        elif task_result.state == "FAILURE":
            response.error = str(task_result.result)
            response.completed_at = datetime.utcnow().isoformat()

        return response

    except Exception as e:
        # Job not found or error querying Celery
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel a running or queued job.

    Gracefully stops job execution and saves partial results.
    """
    try:
        task_result = celery_app.AsyncResult(job_id)

        # Check if job can be cancelled
        if task_result.state in ["SUCCESS", "FAILURE"]:
            raise HTTPException(
                status_code=400,
                detail=f"Job cannot be cancelled (status: {task_result.state})"
            )

        # Revoke task
        celery_app.control.revoke(job_id, terminate=True)

        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully. Partial results may have been saved.",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )


@router.get("", response_model=dict)
async def list_jobs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    created_after: Optional[datetime] = Query(None, description="Filter jobs created after"),
    created_before: Optional[datetime] = Query(None, description="Filter jobs created before"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List background jobs with filtering and pagination.

    Note: This is a simplified implementation. In production, job metadata
    would be stored in a database for efficient querying.
    """
    # This is a placeholder implementation
    # In production, you would:
    # 1. Store job metadata in database
    # 2. Query the database with filters
    # 3. Return paginated results

    # For now, return an empty list with a note
    return {
        "jobs": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "message": "Job listing requires job metadata storage (not yet implemented)",
    }
