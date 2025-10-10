"""Celery application configuration for background job processing."""

from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'hypepaper',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'  # Use Redis backend instead of PostgreSQL for simplicity
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # One task at a time per worker
    beat_schedule={
        'daily-star-tracking': {
            'task': 'jobs.star_tracker.track_daily_stars',
            'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
        },
    },
)

# Import task modules for Celery task discovery
# These imports must come after celery_app creation to avoid circular imports
from . import paper_crawler  # noqa: F401, E402
from . import metadata_enricher  # noqa: F401, E402
from . import star_tracker  # noqa: F401, E402
