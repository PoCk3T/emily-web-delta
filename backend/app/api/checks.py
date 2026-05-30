"""Check results API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.check_result import CheckResult

router = APIRouter()


@router.get("/urls/{url_id}/checks")
async def list_checks(
    url_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
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
async def get_check(url_id: str, check_id: str, db: AsyncSession = Depends(get_session)):
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
async def get_check_diff(url_id: str, check_id: str, db: AsyncSession = Depends(get_session)):
    """Get rendered diff for a check."""
    from fastapi import HTTPException
    from uuid import UUID

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
