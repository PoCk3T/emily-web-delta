"""Diff service layer."""

import logging
from typing import Optional

from app.core.diff_engine import compute_diff
from app.models.diff import Diff
from app.models.snapshot import UrlSnapshot

logger = logging.getLogger(__name__)


class DiffService:
    """Service layer for diff operations."""

    def __init__(self, db_session):
        self.db = db_session

    async def compute_and_store(
        self,
        url_id: str,
        from_snapshot_id: str,
        to_snapshot_id: str,
        diff_type: str = "unified",
    ) -> Optional[Diff]:
        """Compute diff between two snapshots and store it."""
        from sqlalchemy import select

        # Get snapshots
        result = await self.db.execute(
            select(UrlSnapshot).where(UrlSnapshot.id == to_snapshot_id)
        )
        to_snapshot = result.scalar_one_or_none()
        if not to_snapshot:
            return None

        result = await self.db.execute(
            select(UrlSnapshot).where(UrlSnapshot.id == from_snapshot_id)
        )
        from_snapshot = result.scalar_one_or_none()
        if not from_snapshot:
            return None

        # Compute diff
        diff_result = await compute_diff(
            from_snapshot.extracted_text,
            to_snapshot.extracted_text,
        )

        # Store diff
        diff = Diff(
            url_id=url_id,
            snapshot_from_id=from_snapshot_id,
            snapshot_to_id=to_snapshot_id,
            diff_type=diff_type,
            diff_content=diff_result.unified_diff,
            diff_size=diff_result.diff_size,
            lines_added=diff_result.lines_added,
            lines_removed=diff_result.lines_removed,
        )
        self.db.add(diff)
        await self.db.commit()
        await self.db.refresh(diff)
        return diff

    async def get_diffs_for_url(
        self,
        url_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Diff]:
        """Get paginated diffs for a URL."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Diff)
            .where(Diff.url_id == url_id)
            .order_by(Diff.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all())
