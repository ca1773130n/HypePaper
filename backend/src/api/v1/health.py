"""Health check and monitoring endpoints."""
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.cache_service import get_cache

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "hypepaper-api",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check with dependency validation.

    Checks:
        - Database connectivity
        - Redis connectivity

    Returns:
        Readiness status with component details
    """
    checks = {
        "database": "unknown",
        "cache": "unknown",
    }

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            checks["database"] = "healthy"
        else:
            checks["database"] = "unhealthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        cache = get_cache()
        await cache.set("health_check", {"test": True}, ttl=10)
        test_value = await cache.get("health_check")
        if test_value and test_value.get("test") is True:
            checks["cache"] = "healthy"
        else:
            checks["cache"] = "unhealthy"
    except Exception as e:
        checks["cache"] = f"unhealthy: {str(e)}"

    # Determine overall status
    all_healthy = all(v == "healthy" for v in checks.values())
    overall_status = "ready" if all_healthy else "not_ready"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """System metrics endpoint.

    Returns:
        System metrics including database statistics
    """
    from ...models import (
        Author,
        GitHubMetrics,
        LLMExtraction,
        Paper,
        PDFContent,
        PaperReference,
    )

    metrics_data = {}

    try:
        # Count papers
        result = await db.execute(text("SELECT COUNT(*) FROM papers"))
        metrics_data["papers_total"] = result.scalar()

        # Count papers with GitHub repos
        result = await db.execute(
            text("SELECT COUNT(*) FROM papers WHERE github_url IS NOT NULL")
        )
        metrics_data["papers_with_github"] = result.scalar()

        # Count authors
        result = await db.execute(text("SELECT COUNT(*) FROM authors"))
        metrics_data["authors_total"] = result.scalar()

        # Count citations
        result = await db.execute(text("SELECT COUNT(*) FROM paper_references"))
        metrics_data["citations_total"] = result.scalar()

        # Count LLM extractions
        result = await db.execute(text("SELECT COUNT(*) FROM llm_extractions"))
        metrics_data["llm_extractions_total"] = result.scalar()

        # Count LLM extractions by verification status
        result = await db.execute(
            text(
                "SELECT verification_status, COUNT(*) FROM llm_extractions "
                "GROUP BY verification_status"
            )
        )
        verification_counts = {row[0]: row[1] for row in result}
        metrics_data["llm_extractions_by_status"] = verification_counts

        # Count PDFs processed
        result = await db.execute(text("SELECT COUNT(*) FROM pdf_content"))
        metrics_data["pdfs_processed"] = result.scalar()

        # GitHub metrics
        result = await db.execute(
            text("SELECT COUNT(*) FROM github_metrics WHERE current_stars > 0")
        )
        metrics_data["repos_tracked"] = result.scalar()

        result = await db.execute(
            text("SELECT SUM(current_stars) FROM github_metrics")
        )
        total_stars = result.scalar()
        metrics_data["total_stars_tracked"] = total_stars if total_stars else 0

        # Average stars per repo
        if metrics_data["repos_tracked"] > 0:
            metrics_data["avg_stars_per_repo"] = (
                metrics_data["total_stars_tracked"] / metrics_data["repos_tracked"]
            )
        else:
            metrics_data["avg_stars_per_repo"] = 0

        # Most popular tasks
        result = await db.execute(
            text(
                "SELECT primary_task, COUNT(*) as count FROM papers "
                "WHERE primary_task IS NOT NULL "
                "GROUP BY primary_task "
                "ORDER BY count DESC "
                "LIMIT 10"
            )
        )
        top_tasks = [{"task": row[0], "count": row[1]} for row in result]
        metrics_data["top_tasks"] = top_tasks

        # Most used datasets
        result = await db.execute(
            text(
                "SELECT jsonb_array_elements_text(datasets_used) as dataset, "
                "COUNT(*) as count FROM papers "
                "WHERE datasets_used IS NOT NULL "
                "GROUP BY dataset "
                "ORDER BY count DESC "
                "LIMIT 10"
            )
        )
        top_datasets = [{"dataset": row[0], "count": row[1]} for row in result]
        metrics_data["top_datasets"] = top_datasets

    except Exception as e:
        metrics_data["error"] = str(e)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics_data,
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness probe endpoint (minimal dependencies).

    Used by Kubernetes/Docker health checks.

    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
