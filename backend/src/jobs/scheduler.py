"""APScheduler configuration for background jobs.

Schedules daily jobs at 2 AM UTC:
- Paper discovery
- Metric updates
- Topic matching
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .discover_papers import run_discovery_job
from .match_topics import run_topic_matching_job
from .update_metrics import run_metric_update_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for background jobs."""

    def __init__(self):
        """Initialize job scheduler."""
        self.scheduler = AsyncIOScheduler()

    def setup_jobs(self):
        """Configure all scheduled jobs."""

        # Daily paper discovery at 2:00 AM UTC
        self.scheduler.add_job(
            run_discovery_job,
            trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
            id="paper_discovery",
            name="Daily Paper Discovery",
            replace_existing=True,
        )
        logger.info("Scheduled: Paper discovery at 2:00 AM UTC")

        # Daily metric updates at 2:30 AM UTC (after paper discovery)
        self.scheduler.add_job(
            run_metric_update_job,
            trigger=CronTrigger(hour=2, minute=30, timezone="UTC"),
            id="metric_update",
            name="Daily Metric Update",
            replace_existing=True,
        )
        logger.info("Scheduled: Metric update at 2:30 AM UTC")

        # Daily topic matching at 3:00 AM UTC (after both above)
        self.scheduler.add_job(
            run_topic_matching_job,
            trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
            id="topic_matching",
            name="Daily Topic Matching",
            replace_existing=True,
        )
        logger.info("Scheduled: Topic matching at 3:00 AM UTC")

    def start(self):
        """Start the scheduler."""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("Job scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("Job scheduler stopped")


# Global scheduler instance
_scheduler = None


def get_scheduler() -> JobScheduler:
    """Get or create the global scheduler instance.

    Returns:
        JobScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


def start_scheduler():
    """Start the background job scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the background job scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None


async def run_scheduler():
    """Run the scheduler (for standalone execution).

    This keeps the scheduler running indefinitely.
    """
    start_scheduler()

    try:
        # Keep the scheduler running
        while True:
            await asyncio.sleep(60)  # Check every minute
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler interrupted, shutting down...")
        stop_scheduler()


if __name__ == "__main__":
    # Run scheduler standalone
    asyncio.run(run_scheduler())
