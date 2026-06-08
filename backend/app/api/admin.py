"""Admin API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.check_result import CheckResult
from app.models.url import Url
from app.models.user import User

router = APIRouter()


@router.get("/admin/health")
async def admin_health(db: AsyncSession = Depends(get_session)):
    """System health check."""
    return {
        "status": "healthy",
        "urls_count": 0,
        "users_count": 0,
    }


@router.get("/admin/stats")
async def admin_stats(db: AsyncSession = Depends(get_session)):
    """Platform statistics."""
    url_count = await db.execute(select(func.count(Url.id)))
    user_count = await db.execute(select(func.count(User.id)))
    check_count = await db.execute(select(func.count(CheckResult.id)))

    return {
        "total_urls": url_count.scalar() or 0,
        "total_users": user_count.scalar() or 0,
        "total_checks": check_count.scalar() or 0,
        "active_urls": (await db.execute(select(func.count(Url.id)).where(Url.enabled))).scalar() or 0,
    }


@router.get("/admin/urls-overview")
async def urls_overview(db: AsyncSession = Depends(get_session)):
    """All URLs status overview."""
    result = await db.execute(select(Url).order_by(Url.created_at.desc()))
    urls = result.scalars().all()

    return {
        "data": [
            {
                "id": str(u.id),
                "name": u.name,
                "url": u.url,
                "enabled": u.enabled,
                "backend": u.backend,
                "last_checked": u.last_checked.isoformat() if u.last_checked else None,
                "status": "active" if u.enabled else "disabled",
            }
            for u in urls[:100]  # Limit to 100
        ],
        "total": len(urls),
    }


@router.get("/admin/worker-status")
async def worker_status():
    """Celery worker health (self-hosted only)."""
    return {
        "workers": [],
        "status": "not_configured",
        "message": "Celery workers not configured for this deployment",
    }


@router.get("/admin/config")
async def admin_config():
    """System configuration."""
    return {
        "version": "0.1.0",
        "features": {
            "firecrawl": True,
            "selfhosted": True,
            "notifications": True,
            "analytics": True,
        },
    }


@router.get("/admin/audit-log")
async def audit_log(db: AsyncSession = Depends(get_session)):
    """Audit log (admin)."""
    return {
        "message": "Audit log feature coming soon",
        "data": [],
    }
