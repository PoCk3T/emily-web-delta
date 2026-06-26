"""Diff API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.diff import Diff

router = APIRouter()


@router.get("/diffs")
async def list_global_diffs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    url_id: str | None = Query(None, alias="urlId"),
    db: AsyncSession = Depends(get_session),
):
    """List all global diffs with camelCase response formatting for the frontend."""
    from uuid import UUID

    query = select(Diff)
    if url_id:
        query = query.where(Diff.url_id == UUID(url_id))

    query = query.order_by(Diff.created_at.desc())

    result = await db.execute(query)
    all_diffs = result.scalars().all()
    total = len(all_diffs)

    offset = (page - 1) * per_page
    diffs = all_diffs[offset : offset + per_page]

    return {
        "data": {
            "items": [
                {
                    "id": str(d.id),
                    "checkId": str(d.snapshot_to_id),
                    "urlId": str(d.url_id),
                    "previousChecksum": str(d.snapshot_from_id)
                    if d.snapshot_from_id
                    else None,
                    "currentChecksum": str(d.snapshot_to_id),
                    "diffContent": d.diff_content or "",
                    "diffType": d.diff_type,
                    "summary": f"Lines added: {d.lines_added}, lines removed: {d.lines_removed}",
                    "aiSummary": None,
                    "createdAt": d.created_at.isoformat(),
                    "url": d.url.url if d.url else None,
                    "urlName": d.url.name if d.url else None,
                }
                for d in diffs
            ],
            "total": total,
            "page": page,
            "pageSize": per_page,
            "totalPages": (total + per_page - 1) // per_page if total > 0 else 1,
        }
    }


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
    from uuid import UUID

    from fastapi import HTTPException

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
async def get_diff_rendered(
    url_id: str, diff_id: str, db: AsyncSession = Depends(get_session)
):
    """Get rendered HTML diff."""
    from uuid import UUID

    from fastapi import HTTPException

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
async def get_diff_download(
    url_id: str, diff_id: str, db: AsyncSession = Depends(get_session)
):
    """Download diff as HTML/JSON."""
    from uuid import UUID

    from fastapi import HTTPException

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


@router.get("/diffs/{diff_id}")
async def get_global_diff(diff_id: str, db: AsyncSession = Depends(get_session)):
    """Get a specific diff globally wrapped in a {"data": ...} structure."""
    from uuid import UUID

    from fastapi import HTTPException

    result = await db.execute(select(Diff).where(Diff.id == UUID(diff_id)))
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")

    return {
        "data": {
            "id": str(diff.id),
            "checkId": str(diff.snapshot_to_id),
            "urlId": str(diff.url_id),
            "previousChecksum": str(diff.snapshot_from_id)
            if diff.snapshot_from_id
            else None,
            "currentChecksum": str(diff.snapshot_to_id),
            "diffContent": diff.diff_content or "",
            "diffType": diff.diff_type,
            "summary": f"Lines added: {diff.lines_added}, lines removed: {diff.lines_removed}",
            "aiSummary": None,
            "createdAt": diff.created_at.isoformat(),
            "url": diff.url.url if diff.url else None,
            "urlName": diff.url.name if diff.url else None,
        }
    }


@router.get("/diffs/{diff_id}/ai-summary")
async def get_diff_ai_summary(diff_id: str, db: AsyncSession = Depends(get_session)):
    """Get dynamic AI summary for a diff."""
    from uuid import UUID

    from fastapi import HTTPException

    result = await db.execute(select(Diff).where(Diff.id == UUID(diff_id)))
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Diff not found")

    summary_text = f"AI Summary: This update introduced {diff.lines_added} additions and {diff.lines_removed} deletions."

    return {"data": {"summary": summary_text}}
