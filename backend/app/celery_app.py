"""Celery configuration for self-hosted polling."""

import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "emily",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.workers.polling",
        "app.workers.notifications",
        "app.workers.diff_processing",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "poll-urls": {
            "task": "app.workers.polling.poll_urls",
            "schedule": 10,  # Check every 10 seconds
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
