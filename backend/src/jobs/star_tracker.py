"""
Scheduled background job for daily GitHub star tracking.

Celery task that runs daily at 2 AM UTC to update star counts for all
papers with GitHub repositories, create snapshots, and calculate hype scores.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from ..database import AsyncSessionLocal
from ..services.github_service import AsyncGitHubService
from ..models.paper import Paper


logger = logging.getLogger(__name__)


@celery_app.task(name='jobs.star_tracker.track_daily_stars')
def track_daily_stars() -> Dict[str, Any]:
    """
    Scheduled task: Update GitHub star counts for all papers with repos.

    Runs: Daily at 2 AM UTC (configured in celery_app.py beat_schedule)
    Rate limit: Respects GitHub API limit (5000 req/hour for authenticated)

    Steps:
    1. Get all papers with github_url
    2. For each paper:
       a. Fetch current star count via GitHub API
       b. Create GitHubStarSnapshot record
       c. Calculate hype scores (avg/weekly/monthly)
       d. Update paper's cached star count and hype scores
    3. Return summary statistics

    Returns:
        Dict with status, papers_updated, errors count

    Example:
        >>> track_daily_stars.delay()  # Triggered by Celery Beat scheduler
    """
    logger.info("Starting daily GitHub star tracking task")

    try:
        # Run async task in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _async_track_stars()
        )

        return result

    except Exception as e:
        logger.error(f"Daily star tracking failed: {e}", exc_info=True)
        raise


async def _async_track_stars() -> Dict[str, Any]:
    """
    Async implementation of daily star tracking.

    Returns:
        Dict with tracking results and statistics
    """
    papers_updated = 0
    errors = 0
    total_stars_tracked = 0

    # Create database session
    async with AsyncSessionLocal() as session:
        try:
            # Get all papers with GitHub URLs
            result = await session.execute(
                select(Paper).where(Paper.github_url.isnot(None))
            )
            papers_with_github = result.scalars().all()

            total_papers = len(papers_with_github)
            logger.info(f"Found {total_papers} papers with GitHub repositories")

            if total_papers == 0:
                return {
                    'status': 'completed',
                    'papers_updated': 0,
                    'errors': 0,
                    'message': 'No papers with GitHub URLs found'
                }

            # Initialize GitHub service
            github_service = AsyncGitHubService()

            # Process each paper
            for i, paper in enumerate(papers_with_github, 1):
                try:
                    logger.info(f"Processing {i}/{total_papers}: {paper.title}")

                    # Fetch current star count
                    current_stars = await github_service.get_star_count(paper.github_url)

                    if current_stars == 0:
                        logger.warning(f"Failed to fetch stars for {paper.github_url}")
                        errors += 1
                        continue

                    logger.info(f"Current stars: {current_stars}")
                    total_stars_tracked += current_stars

                    # Create GitHubMetrics snapshot
                    # In production: create GitHubMetrics model instance
                    snapshot_data = {
                        'paper_id': paper.id,
                        'repo_url': paper.github_url,
                        'star_count': current_stars,
                        'timestamp': datetime.utcnow()
                    }
                    logger.debug(f"Would create GitHubMetrics snapshot: {snapshot_data}")

                    # Get historical star data for hype calculation
                    # In production: query GitHubMetrics table
                    star_history = await _get_star_history(session, paper.id)

                    # Add current snapshot to history
                    star_history.append({
                        'timestamp': datetime.utcnow(),
                        'stars': current_stars,
                        'citations': 0  # TODO: Get citation count from paper
                    })

                    # Calculate hype scores
                    hype_scores = await github_service.calculate_hype_scores(star_history)
                    logger.info(f"Hype scores: {hype_scores}")

                    # Update paper's cached metrics
                    # In production: update Paper model fields
                    paper.github_star_count = current_stars
                    # paper.avg_hype = hype_scores['avg_hype']
                    # paper.weekly_hype = hype_scores['weekly_hype']
                    # paper.monthly_hype = hype_scores['monthly_hype']

                    papers_updated += 1

                    # Rate limiting: Sleep between requests to respect API limits
                    # 5000 req/hour = ~1.4 req/sec, so we sleep 1 second
                    if i < total_papers:
                        await asyncio.sleep(1.0)

                except Exception as e:
                    logger.error(f"Error processing paper {paper.id}: {e}", exc_info=True)
                    errors += 1
                    continue

            # Commit all changes
            await session.commit()

            logger.info(
                f"Star tracking complete: {papers_updated} updated, "
                f"{errors} errors, {total_stars_tracked} total stars tracked"
            )

            return {
                'status': 'completed',
                'papers_updated': papers_updated,
                'errors': errors,
                'total_papers': total_papers,
                'total_stars_tracked': total_stars_tracked,
                'avg_stars_per_paper': total_stars_tracked / papers_updated if papers_updated > 0 else 0,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            await session.rollback()
            raise


async def _get_star_history(
    session: AsyncSession,
    paper_id: Any
) -> List[Dict[str, Any]]:
    """
    Get historical star data for hype score calculation.

    In production, this would query the GitHubMetrics table.
    For now, returns empty list (first-time tracking).

    Args:
        session: Database session
        paper_id: Paper UUID

    Returns:
        List of star history entries with timestamp, stars, citations
    """
    # TODO: Implement actual query when GitHubMetrics model is available
    # Example query:
    # result = await session.execute(
    #     select(GitHubMetrics)
    #     .where(GitHubMetrics.paper_id == paper_id)
    #     .order_by(GitHubMetrics.timestamp.asc())
    # )
    # metrics = result.scalars().all()
    # return [
    #     {
    #         'timestamp': m.timestamp,
    #         'stars': m.star_count,
    #         'citations': 0  # Get from paper citations
    #     }
    #     for m in metrics
    # ]

    logger.debug(f"Star history query not yet implemented for paper {paper_id}")
    return []
