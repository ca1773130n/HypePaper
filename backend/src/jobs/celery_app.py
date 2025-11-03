"""Celery application configuration for background job processing."""

import os
from celery import Celery
from celery.schedules import crontab

# Use environment variable for Redis URL, or None to disable Celery
# Note: This project now uses Cloudflare Workers + Upstash for async jobs
# Celery is optional and only needed for scheduled tasks
REDIS_URL = os.getenv('REDIS_URL')

celery_app = Celery(
    'hypepaper',
    broker=REDIS_URL or 'redis://localhost:6379/0',
    backend=REDIS_URL or 'redis://localhost:6379/1'
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
