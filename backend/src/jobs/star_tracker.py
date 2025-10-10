"""
Scheduled background job for daily GitHub star tracking.

Celery task that runs daily at 2 AM UTC to update star counts for all
papers with GitHub repositories, create snapshots, and calculate hype scores.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from ..database import AsyncSessionLocal
from ..services.github_service import AsyncGitHubService
from ..models.paper import Paper
from ..models.github_metrics import GitHubMetrics, GitHubStarSnapshot


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

                    # Fetch current star count and repo details from GitHub API
                    repo_details = await github_service._get_repo_details(paper.github_url)

                    if not repo_details:
                        logger.warning(f"Failed to fetch repo details for {paper.github_url}")
                        errors += 1
                        continue

                    current_stars = repo_details.stars
                    logger.info(f"Current stars: {current_stars}")
                    total_stars_tracked += current_stars

                    # Extract owner and repo name from URL
                    parts = paper.github_url.rstrip('/').split('/')
                    repo_owner = parts[-2] if len(parts) >= 2 else ""
                    repo_name = parts[-1] if len(parts) >= 1 else ""

                    # Get or create GitHubMetrics record
                    result = await session.execute(
                        select(GitHubMetrics).where(GitHubMetrics.paper_id == paper.id)
                    )
                    github_metrics = result.scalar_one_or_none()

                    today = date.today()

                    if not github_metrics:
                        # Create new GitHubMetrics record
                        github_metrics = GitHubMetrics(
                            paper_id=paper.id,
                            repository_url=paper.github_url,
                            repository_owner=repo_owner,
                            repository_name=repo_name,
                            current_stars=current_stars,
                            current_forks=0,  # Can be extended to track forks
                            current_watchers=0,  # Can be extended to track watchers
                            tracking_start_date=today,
                            last_tracked_at=datetime.utcnow(),
                            tracking_enabled=True
                        )
                        session.add(github_metrics)
                        logger.info(f"Created new GitHubMetrics for {paper.title}")
                    else:
                        # Update existing record
                        github_metrics.current_stars = current_stars
                        github_metrics.last_tracked_at = datetime.utcnow()
                        logger.debug(f"Updated GitHubMetrics for {paper.title}")

                    # Create daily star snapshot
                    # Check if snapshot already exists for today
                    result = await session.execute(
                        select(GitHubStarSnapshot).where(
                            GitHubStarSnapshot.paper_id == paper.id,
                            GitHubStarSnapshot.snapshot_date == today
                        )
                    )
                    existing_snapshot = result.scalar_one_or_none()

                    if not existing_snapshot:
                        # Get yesterday's star count for delta calculation
                        yesterday = today - timedelta(days=1)
                        result = await session.execute(
                            select(GitHubStarSnapshot).where(
                                GitHubStarSnapshot.paper_id == paper.id,
                                GitHubStarSnapshot.snapshot_date == yesterday
                            )
                        )
                        yesterday_snapshot = result.scalar_one_or_none()

                        stars_gained = None
                        if yesterday_snapshot:
                            stars_gained = current_stars - yesterday_snapshot.star_count

                        # Create new snapshot
                        snapshot = GitHubStarSnapshot(
                            paper_id=paper.id,
                            snapshot_date=today,
                            star_count=current_stars,
                            fork_count=0,
                            watcher_count=0,
                            stars_gained_since_yesterday=stars_gained
                        )
                        session.add(snapshot)
                        logger.debug(f"Created GitHubStarSnapshot for {paper.title}: {current_stars} stars")
                    else:
                        logger.debug(f"Snapshot already exists for today for {paper.title}")

                    # Get historical star data for hype calculation
                    star_history = await _get_star_history(session, paper.id)

                    # Add current snapshot to history for calculation
                    star_history.append({
                        'timestamp': datetime.utcnow(),
                        'stars': current_stars,
                        'citations': 0  # TODO: Get citation count from paper when available
                    })

                    # Calculate hype scores using SOTAPapers formula
                    hype_scores = _calculate_hype_scores(
                        star_history=star_history,
                        tracking_start_date=github_metrics.tracking_start_date
                    )
                    logger.info(f"Hype scores: {hype_scores}")

                    # Update GitHubMetrics with calculated hype scores
                    github_metrics.average_hype = hype_scores['avg_hype']
                    github_metrics.weekly_hype = hype_scores['weekly_hype']
                    github_metrics.monthly_hype = hype_scores['monthly_hype']

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

    Queries GitHubStarSnapshot table for all historical snapshots.

    Args:
        session: Database session
        paper_id: Paper UUID

    Returns:
        List of star history entries with timestamp, stars, citations
    """
    result = await session.execute(
        select(GitHubStarSnapshot)
        .where(GitHubStarSnapshot.paper_id == paper_id)
        .order_by(GitHubStarSnapshot.snapshot_date.asc())
    )
    snapshots = result.scalars().all()

    star_history = [
        {
            'timestamp': datetime.combine(snapshot.snapshot_date, datetime.min.time()),
            'stars': snapshot.star_count,
            'citations': 0  # TODO: Get from paper citations when available
        }
        for snapshot in snapshots
    ]

    logger.debug(f"Retrieved {len(star_history)} historical snapshots for paper {paper_id}")
    return star_history


def _calculate_hype_scores(
    star_history: List[Dict[str, Any]],
    tracking_start_date: date
) -> Dict[str, float]:
    """
    Calculate hype scores based on star history using SOTAPapers formula.

    Formula from SOTAPapers (_update_paper_metrics):
    - If citations > 0: hype = (citations * 100 + stars) / age_days
    - If citations == 0: hype = stars / age_days

    Args:
        star_history: List of dicts with 'timestamp', 'stars', 'citations'
        tracking_start_date: Date when tracking began (repository creation date)

    Returns:
        Dict with avg_hype, weekly_hype, monthly_hype
    """
    if not star_history or len(star_history) == 0:
        return {
            'avg_hype': 0.0,
            'weekly_hype': 0.0,
            'monthly_hype': 0.0
        }

    # Sort by timestamp
    sorted_history = sorted(star_history, key=lambda x: x['timestamp'])

    # Calculate overall average hype (from tracking start to now)
    latest_entry = sorted_history[-1]
    latest_stars = latest_entry.get('stars', 0)
    latest_citations = latest_entry.get('citations', 0)

    # Calculate age in days from tracking start date
    age_days = max(1, (date.today() - tracking_start_date).days)

    if latest_citations > 0:
        avg_hype = (latest_citations * 100 + latest_stars) / age_days
    else:
        avg_hype = latest_stars / age_days if latest_stars > 0 else 0.0

    # Calculate weekly hype (last 7 days)
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    recent_weekly = [e for e in sorted_history if e['timestamp'] >= week_ago]

    if len(recent_weekly) >= 2:
        latest = recent_weekly[-1]
        oldest = recent_weekly[0]
        star_growth = latest.get('stars', 0) - oldest.get('stars', 0)
        citation_growth = latest.get('citations', 0) - oldest.get('citations', 0)

        if citation_growth > 0:
            weekly_hype = (citation_growth * 100 + star_growth) / 7
        else:
            weekly_hype = star_growth / 7 if star_growth > 0 else 0.0
    elif len(recent_weekly) == 1:
        # Only one data point in the last week
        entry = recent_weekly[0]
        days_since = max(1, (now - entry['timestamp']).days)
        stars = entry.get('stars', 0)
        citations = entry.get('citations', 0)

        if citations > 0:
            weekly_hype = (citations * 100 + stars) / days_since
        else:
            weekly_hype = stars / days_since if stars > 0 else 0.0
    else:
        weekly_hype = 0.0

    # Calculate monthly hype (last 30 days)
    month_ago = now - timedelta(days=30)
    recent_monthly = [e for e in sorted_history if e['timestamp'] >= month_ago]

    if len(recent_monthly) >= 2:
        latest = recent_monthly[-1]
        oldest = recent_monthly[0]
        star_growth = latest.get('stars', 0) - oldest.get('stars', 0)
        citation_growth = latest.get('citations', 0) - oldest.get('citations', 0)

        if citation_growth > 0:
            monthly_hype = (citation_growth * 100 + star_growth) / 30
        else:
            monthly_hype = star_growth / 30 if star_growth > 0 else 0.0
    elif len(recent_monthly) == 1:
        # Only one data point in the last month
        entry = recent_monthly[0]
        days_since = max(1, (now - entry['timestamp']).days)
        stars = entry.get('stars', 0)
        citations = entry.get('citations', 0)

        if citations > 0:
            monthly_hype = (citations * 100 + stars) / days_since
        else:
            monthly_hype = stars / days_since if stars > 0 else 0.0
    else:
        monthly_hype = 0.0

    return {
        'avg_hype': round(avg_hype, 2),
        'weekly_hype': round(weekly_hype, 2),
        'monthly_hype': round(monthly_hype, 2)
    }
