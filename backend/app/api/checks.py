"""Check results API routes."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.check_result import CheckResult

router = APIRouter()


@router.get("/checks")
async def list_global_checks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    urlId: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """List all global check results with camelCase key responses for the frontend."""
    from uuid import UUID

    query = select(CheckResult)
    if urlId:
        query = query.where(CheckResult.url_id == UUID(urlId))

    query = query.order_by(CheckResult.created_at.desc())

    result = await db.execute(query)
    all_checks = result.scalars().all()
    total = len(all_checks)

    offset = (page - 1) * per_page
    checks = all_checks[offset : offset + per_page]

    return {
        "data": {
            "items": [
                {
                    "id": str(c.id),
                    "urlId": str(c.url_id),
                    "url": c.url.url if c.url else "N/A",
                    "urlName": c.url.name if c.url else "N/A",
                    "status": c.status,
                    "statusCode": c.status_code
                    or (200 if c.status == "completed" else 500),
                    "contentLength": c.diff_size or 0,
                    "checksum": c.content_hash,
                    "pageTitle": c.judgment.get("title")
                    if (c.judgment and isinstance(c.judgment, dict))
                    else "N/A",
                    "loadTime": c.check_duration_ms or 100,
                    "error": c.error_message,
                    "startedAt": c.created_at.isoformat(),
                    "completedAt": c.created_at.isoformat(),
                    "createdAt": c.created_at.isoformat(),
                }
                for c in checks
            ],
            "total": total,
            "page": page,
            "pageSize": per_page,
            "totalPages": (total + per_page - 1) // per_page if total > 0 else 1,
        }
    }


@router.get("/urls/{url_id}/checks")
async def list_checks(
    url_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """List check results for a URL."""
    from uuid import UUID

    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.url_id == UUID(url_id))
        .order_by(CheckResult.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    checks = result.scalars().all()

    return {
        "data": [
            {
                "id": str(c.id),
                "check_id": c.check_id,
                "backend": c.backend,
                "status": c.status,
                "is_meaningful": c.is_meaningful,
                "judgment": c.judgment,
                "diff_size": c.diff_size,
                "error_message": c.error_message,
                "created_at": c.created_at.isoformat(),
            }
            for c in checks
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(checks),
        },
    }


@router.get("/urls/{url_id}/checks/{check_id}")
async def get_check(
    url_id: str, check_id: str, db: AsyncSession = Depends(get_session)
):
    """Get a specific check result."""
    from uuid import UUID

    result = await db.execute(
        select(CheckResult).where(
            CheckResult.id == UUID(check_id),
            CheckResult.url_id == UUID(url_id),
        )
    )
    check = result.scalar_one_or_none()
    if not check:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Check not found")

    return {
        "id": str(check.id),
        "url_id": str(check.url_id),
        "check_id": check.check_id,
        "backend": check.backend,
        "status": check.status,
        "is_meaningful": check.is_meaningful,
        "judgment": check.judgment,
        "diff_text": check.diff_text,
        "diff_json": check.diff_json,
        "diff_size": check.diff_size,
        "snapshot_json": check.snapshot_json,
        "error_message": check.error_message,
        "created_at": check.created_at.isoformat(),
    }


@router.get("/urls/{url_id}/checks/{check_id}/diff")
async def get_check_diff(
    url_id: str, check_id: str, db: AsyncSession = Depends(get_session)
):
    """Get rendered diff for a check."""
    from uuid import UUID

    from fastapi import HTTPException

    result = await db.execute(
        select(CheckResult).where(
            CheckResult.id == UUID(check_id),
            CheckResult.url_id == UUID(url_id),
        )
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    return {
        "check_id": check.check_id,
        "status": check.status,
        "diff_text": check.diff_text or "",
        "diff_json": check.diff_json or {},
        "judgment": check.judgment,
    }
