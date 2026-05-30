"""Celery tasks for self-hosted polling."""

import logging

from app.celery_app import celery_app
from app.services.check_service import CheckService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
async def poll_urls(self, url_ids: list[str]):
    """Poll a batch of URLs."""
    logger.info(f"Polling {len(url_ids)} URLs")
    # Implementation would import and use CheckService
    return {"polled": len(url_ids)}


@celery_app.task
async def process_diff(self, diff_id: str):
    """Process a diff."""
    logger.info(f"Processing diff {diff_id}")
    return {"processed": diff_id}


@celery_app.task
async def send_notifications(self, rule_ids: list[str]):
    """Send notifications for a batch of rules."""
    logger.info(f"Sending notifications for {len(rule_ids)} rules")
    return {"sent": len(rule_ids)}
