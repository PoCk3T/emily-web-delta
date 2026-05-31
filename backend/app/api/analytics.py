"""Analytics API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.check_result import CheckResult

router = APIRouter()


@router.get("/urls/{url_id}/analytics")
async def url_analytics(
    url_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_session),
):
    """Change frequency, trends, anomalies for a URL."""
    from uuid import UUID

    # Count checks in the period
    result = await db.execute(
        select(func.count(CheckResult.id)).where(
            CheckResult.url_id == UUID(url_id),
            CheckResult.created_at >= func.now() - func.interval(f"{days} days"),
        )
    )
    total_checks = result.scalar() or 0

    # Count changes
    result = await db.execute(
        select(func.count(CheckResult.id)).where(
            CheckResult.url_id == UUID(url_id),
            CheckResult.created_at >= func.now() - func.interval(f"{days} days"),
            CheckResult.status == "changed",
        )
    )
    total_changes = result.scalar() or 0

    # Change frequency
    frequency = total_changes / max(days, 1)

    # Trend detection (simple: compare recent vs older changes)
    half_days = days // 2
    result = await db.execute(
        select(func.count(CheckResult.id)).where(
            CheckResult.url_id == UUID(url_id),
            CheckResult.created_at >= func.now() - func.interval(f"{half_days} days"),
            CheckResult.status == "changed",
        )
    )
    recent_changes = result.scalar() or 0

    result = await db.execute(
        select(func.count(CheckResult.id)).where(
            CheckResult.url_id == UUID(url_id),
            CheckResult.created_at < func.now() - func.interval(f"{half_days} days"),
            CheckResult.created_at >= func.now() - func.interval(f"{days} days"),
            CheckResult.status == "changed",
        )
    )
    older_changes = result.scalar() or 0

    trend = "stable"
    if older_changes > 0 and recent_changes > older_changes * 1.5:
        trend = "increasing"
    elif older_changes > 0 and recent_changes < older_changes * 0.5:
        trend = "decreasing"

    # Anomaly detection
    anomaly = None
    if frequency > 5:  # More than 5 changes per day is anomalous
        anomaly = {
            "type": "high_frequency",
            "message": f"Unusually high change frequency: {frequency:.1f}/day",
        }

    return {
        "url_id": url_id,
        "period_days": days,
        "total_checks": total_checks,
        "total_changes": total_changes,
        "change_frequency": round(frequency, 2),
        "trend": trend,
        "recent_changes": recent_changes,
        "older_changes": older_changes,
        "anomaly": anomaly,
    }


@router.get("/urls/analytics")
async def platform_analytics(
    db: AsyncSession = Depends(get_session),
):
    """Platform-wide analytics."""
    from app.models.diff import Diff

    result = await db.execute(select(func.count(CheckResult.id)))
    total_checks = result.scalar() or 0

    # Query the actual count of Diff records in the url_diffs table
    result = await db.execute(select(func.count(Diff.id)))
    total_changes = result.scalar() or 0

    return {
        "total_checks": total_checks,
        "total_changes": total_changes,
        "change_rate": round(total_changes / max(total_checks, 1), 4),
    }


@router.get("/urls/analytics/export")
async def export_analytics(db: AsyncSession = Depends(get_session)):
    """Export analytics data."""
    return {
        "message": "Export feature coming soon",
        "data": [],
    }
