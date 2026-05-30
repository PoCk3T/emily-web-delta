"""Diff API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.diff import Diff

router = APIRouter()


@router.get("/urls/{url_id}/diffs")
async def list_diffs(
    url_id: str,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_session),
):
    """List diffs for a URL."""
    from uuid import UUID

    result = await db.execute(
        select(Diff)
        .where(Diff.url_id == UUID(url_id))
        .order_by(Diff.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    diffs = result.scalars().all()

    return {
        "data": [
            {
                "id": str(d.id),
                "diff_type": d.diff_type,
                "diff_size": d.diff_size,
                "lines_added": d.lines_added,
                "lines_removed": d.lines_removed,
                "created_at": d.created_at.isoformat(),
            }
            for d in diffs
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(diffs),
        },
    }


@router.get("/urls/{url_id}/diffs/{diff_id}")
async def get_diff(url_id: str, diff_id: str, db: AsyncSession = Depends(get_session)):
    """Get a specific diff."""
    from fastapi import HTTPException
    from uuid import UUID

    result = await db.execute(
        select(Diff).where(
            Diff.id == UUID(diff_id),
            Diff.url_id == UUID(url_id),
        )
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")

    return {
        "id": str(diff.id),
        "url_id": str(diff.url_id),
        "diff_type": diff.diff_type,
        "diff_content": diff.diff_content,
        "diff_size": diff.diff_size,
        "lines_added": diff.lines_added,
        "lines_removed": diff.lines_removed,
        "created_at": diff.created_at.isoformat(),
    }


@router.get("/urls/{url_id}/diffs/{diff_id}/rendered")
async def get_diff_rendered(url_id: str, diff_id: str, db: AsyncSession = Depends(get_session)):
    """Get rendered HTML diff."""
    from fastapi import HTTPException
    from uuid import UUID

    result = await db.execute(
        select(Diff).where(
            Diff.id == UUID(diff_id),
            Diff.url_id == UUID(url_id),
        )
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")

    # Return the diff content as-is (could be HTML, JSON, etc.)
    return {
        "diff_type": diff.diff_type,
        "rendered": diff.diff_content,
    }


@router.get("/urls/{url_id}/diffs/{diff_id}/download")
async def get_diff_download(url_id: str, diff_id: str, db: AsyncSession = Depends(get_session)):
    """Download diff as HTML/JSON."""
    from fastapi import HTTPException
    from uuid import UUID

    result = await db.execute(
        select(Diff).where(
            Diff.id == UUID(diff_id),
            Diff.url_id == UUID(url_id),
        )
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")

    return {
        "download_url": f"/api/v1/diffs/{diff_id}/content",
        "format": diff.diff_type,
    }
