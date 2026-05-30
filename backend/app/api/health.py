"""Health check API routes."""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import get_session

router = APIRouter()


@router.get("/health")
async def health_check():
    """Liveness probe - basic health check."""
    return {"status": "ok", "service": "emily-web-delta"}


@router.get("/ready")
async def readiness_check():
    """Readiness probe - checks dependencies."""
    from app.db.session import async_engine

    checks = {}

    # Check database
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Overall status
    status = "healthy" if all(c == "ok" for c in checks.values()) else "degraded"

    return {"status": status, "checks": checks}
