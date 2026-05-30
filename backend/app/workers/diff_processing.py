"""Celery tasks for diff processing."""

import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
async def compute_diff(self, from_snapshot_id: str, to_snapshot_id: str):
    """Compute diff between two snapshots."""
    logger.info(f"Computing diff {from_snapshot_id} -> {to_snapshot_id}")
    return {"diff_computed": True}


@celery_app.task
async def store_diff(self, diff_id: str):
    """Store a computed diff."""
    logger.info(f"Storing diff {diff_id}")
    return {"stored": diff_id}
