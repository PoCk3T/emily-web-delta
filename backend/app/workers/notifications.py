"""Celery tasks for notification dispatch."""

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
async def dispatch_notification(self, rule_id: str, message: str):
    """Dispatch a notification."""
    logger.info(f"Dispatching notification {rule_id}")
    return {"dispatched": rule_id}
