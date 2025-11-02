"""
API endpoints for async crawler job management via Cloudflare Workers + Upstash Redis.

This is separate from the existing Celery-based jobs system in jobs.py.
These endpoints use Cloudflare Workers for serverless job processing.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_user
from ...core.database import get_db
from ...services.job_queue_service import JobQueueService

router = APIRouter(prefix="/async-jobs", tags=["Async Crawler Jobs"])


# Request/Response models
class EnqueueJobRequest(BaseModel):
    """Request to enqueue a crawler job."""

    job_type: str = Field(..., description="Job type: arxiv, github, semantic_scholar")
    params: Dict[str, Any] = Field(
        ..., description="Job parameters (query, url, limit, etc.)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "job_type": "arxiv",
                    "params": {"query": "machine learning", "limit": 10},
                },
                {
                    "job_type": "github",
                    "params": {"url": "https://github.com/pytorch/pytorch"},
                },
            ]
        }


class EnqueueJobResponse(BaseModel):
    """Response after enqueueing a job."""

    success: bool
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Response with job status."""

    id: str
    status: str = Field(
        ..., description="Job status: queued, processing, success, failed, cancelled"
    )
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    processed_at: Optional[str] = None
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    """Response with job results."""

    job_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processed_at: Optional[str] = None


class QueueStatsResponse(BaseModel):
    """Response with queue statistics."""

    queue_length: int
    timestamp: str


class JobWebhookPayload(BaseModel):
    """Webhook payload from Cloudflare Worker."""

    job_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processed_at: str


# Endpoints
@router.post("/enqueue", response_model=EnqueueJobResponse)
async def enqueue_crawler_job(
    request: EnqueueJobRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enqueue a crawler job for async processing via Cloudflare Workers.

    The job will be processed by the Cloudflare Worker within 1 minute.
    This is separate from the Celery-based job system.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user_id = str(current_user["id"])

    # Validate job type
    valid_types = ["arxiv", "github", "semantic_scholar"]
    if request.job_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        service = JobQueueService()
        job_id = await service.enqueue_crawler_job(
            job_type=request.job_type,
            params=request.params,
            user_id=user_id,
        )

        return EnqueueJobResponse(
            success=True,
            job_id=job_id,
            message="Job queued successfully. It will be processed within 1 minute.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job: {str(e)}",
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get status of an async crawler job.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        service = JobQueueService()
        status_data = await service.get_job_status(job_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        return JobStatusResponse(**status_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )


@router.get("/result/{job_id}", response_model=JobResultResponse)
async def get_job_result(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get result of a completed async crawler job.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        service = JobQueueService()
        result = await service.get_job_result(job_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job result not found. Job may still be processing or queued.",
            )

        return JobResultResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job result: {str(e)}",
        )


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get statistics about the async job queue.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        service = JobQueueService()
        stats = await service.get_queue_stats()
        return QueueStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}",
        )


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel a queued job (best effort - only works if not yet processed).
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        service = JobQueueService()
        success = await service.cancel_job(job_id)

        if not success:
            return {
                "success": False,
                "message": "Job not found or already processed",
            }

        return {
            "success": True,
            "message": "Job cancelled successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        )


@router.post("/webhook")
async def job_webhook(payload: JobWebhookPayload):
    """
    Webhook endpoint for Cloudflare Worker to notify job completion.

    This endpoint is called by the worker when a job finishes processing.
    No authentication required as it's called from Cloudflare Worker.
    """
    # TODO: Implement webhook validation (e.g., shared secret, signature)
    # TODO: Store job results in database
    # TODO: Send notifications to user

    print(f"Job webhook received: {payload.job_id} - {payload.status}")

    return {"success": True, "message": "Webhook received"}
