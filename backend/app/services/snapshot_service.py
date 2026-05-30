"""Snapshot service layer."""

import logging
from typing import Optional

from app.models.snapshot import UrlSnapshot
from app.models.url import Url

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service layer for snapshot operations."""

    def __init__(self, db_session):
        self.db = db_session

    async def create_snapshot(
        self,
        url_id: str,
        content: str,
        extracted_text: str,
        content_hash: str,
        content_type: str = "markdown",
    ) -> UrlSnapshot:
        """Create a new snapshot."""
        snapshot = UrlSnapshot(
            url_id=url_id,
            content=content,
            extracted_text=extracted_text,
            content_hash=content_hash,
            content_type=content_type,
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(self, url_id: str) -> Optional[UrlSnapshot]:
        """Get the latest snapshot for a URL."""
        from sqlalchemy import select
        from app.models.snapshot import UrlSnapshot as SnapshotModel

        result = await self.db.execute(
            select(SnapshotModel)
            .where(SnapshotModel.url_id == url_id)
            .order_by(SnapshotModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_snapshots(
        self,
        url_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> list[UrlSnapshot]:
        """Get paginated snapshots."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(UrlSnapshot)
            .where(UrlSnapshot.url_id == url_id)
            .order_by(UrlSnapshot.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all())

    async def prune_old_snapshots(self, url_id: str, keep: int = 30) -> int:
        """Prune old snapshots, keeping only the latest N."""
        from sqlalchemy import select, delete

        result = await self.db.execute(
            select(UrlSnapshot)
            .where(UrlSnapshot.url_id == url_id)
            .order_by(UrlSnapshot.created_at.desc())
            .offset(keep)
        )
        snapshots_to_delete = list(result.scalars().all())

        for snapshot in snapshots_to_delete:
            await self.db.delete(snapshot)

        await self.db.commit()
        return len(snapshots_to_delete)
