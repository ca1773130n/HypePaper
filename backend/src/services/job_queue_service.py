"""
Job Queue Service for async crawler job management using Upstash Redis.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from upstash_redis import Redis


class JobQueueService:
    """Service for managing crawler jobs in Upstash Redis queue."""

    def __init__(self):
        """Initialize Redis connection."""
        redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
        redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

        if not redis_url or not redis_token:
            raise ValueError(
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set"
            )

        self.redis = Redis(url=redis_url, token=redis_token)

    async def enqueue_crawler_job(
        self,
        job_type: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """
        Enqueue a crawler job to the Redis queue.

        Args:
            job_type: Type of crawler job ('arxiv', 'github', 'semantic_scholar')
            params: Job parameters (query, url, limit, etc.)
            user_id: Optional user ID who submitted the job

        Returns:
            Job ID

        Example:
            >>> service = JobQueueService()
            >>> job_id = await service.enqueue_crawler_job(
            ...     job_type='arxiv',
            ...     params={'query': 'machine learning', 'limit': 10},
            ...     user_id='user-123'
            ... )
        """
        job_id = str(uuid4())
        job_data = {
            "id": job_id,
            "type": job_type,
            "params": params,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": 0,
        }

        # Add to queue (RPUSH adds to end, LPOP removes from beginning - FIFO)
        self.redis.rpush("crawler:queue", json.dumps(job_data))

        # Store job metadata with 1 hour TTL
        self.redis.setex(
            f"crawler:job:{job_id}",
            3600,
            json.dumps({**job_data, "status": "queued"}),
        )

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a crawler job.

        Args:
            job_id: Job ID

        Returns:
            Job data with status, or None if not found

        Example:
            >>> service = JobQueueService()
            >>> status = await service.get_job_status('job-123')
            >>> print(status['status'])  # 'queued', 'processing', 'success', 'failed'
        """
        # Check job metadata
        job_data = self.redis.get(f"crawler:job:{job_id}")
        if job_data:
            return json.loads(job_data)

        # Check if result exists
        result_data = self.redis.get(f"crawler:result:{job_id}")
        if result_data:
            result = json.loads(result_data)
            return {
                "id": job_id,
                "status": result["status"],
                "processed_at": result["processed_at"],
                "results": result.get("results"),
                "error": result.get("error"),
            }

        return None

    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result of a completed crawler job.

        Args:
            job_id: Job ID

        Returns:
            Job result data, or None if not found

        Example:
            >>> service = JobQueueService()
            >>> result = await service.get_job_result('job-123')
            >>> if result and result['status'] == 'success':
            ...     papers = result['results']['papers']
        """
        result_data = self.redis.get(f"crawler:result:{job_id}")
        if result_data:
            return json.loads(result_data)
        return None

    async def get_queue_length(self) -> int:
        """
        Get current length of the job queue.

        Returns:
            Number of jobs in queue

        Example:
            >>> service = JobQueueService()
            >>> length = await service.get_queue_length()
            >>> print(f"Jobs in queue: {length}")
        """
        return self.redis.llen("crawler:queue")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the job queue.

        Returns:
            Dictionary with queue statistics

        Example:
            >>> service = JobQueueService()
            >>> stats = await service.get_queue_stats()
            >>> print(f"Queue length: {stats['queue_length']}")
        """
        queue_length = await self.get_queue_length()

        return {
            "queue_length": queue_length,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued job (best effort - only works if not yet processed).

        Args:
            job_id: Job ID to cancel

        Returns:
            True if job was found and marked as cancelled

        Example:
            >>> service = JobQueueService()
            >>> success = await service.cancel_job('job-123')
        """
        job_data = self.redis.get(f"crawler:job:{job_id}")
        if not job_data:
            return False

        job = json.loads(job_data)
        if job.get("status") not in ["queued", "processing"]:
            return False

        # Mark as cancelled
        job["status"] = "cancelled"
        job["cancelled_at"] = datetime.utcnow().isoformat()
        self.redis.setex(f"crawler:job:{job_id}", 3600, json.dumps(job))

        return True
