"""Analytics service layer."""

import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for analytics operations."""

    def __init__(self, db_session):
        self.db = db_session

    async def get_url_analytics(
        self,
        url_id: str,
        days: int = 30,
    ) -> dict:
        """Get analytics for a URL."""
        from sqlalchemy import func, select

        from app.models.check_result import CheckResult

        # Count total checks
        result = await self.db.execute(
            select(func.count(CheckResult.id))
            .where(CheckResult.url_id == url_id)
        )
        total_checks = result.scalar() or 0

        # Count changes
        result = await self.db.execute(
            select(func.count(CheckResult.id))
            .where(
                CheckResult.url_id == url_id,
                CheckResult.status == "changed",
            )
        )
        total_changes = result.scalar() or 0

        # Calculate frequency
        frequency = total_changes / max(days, 1)

        # Trend detection
        result = await self.db.execute(
            select(func.count(CheckResult.id))
            .where(
                CheckResult.url_id == url_id,
                CheckResult.status == "changed",
            )
        )
        _recent_changes = result.scalar() or 0

        trend = "stable"
        if total_changes > 0:
            if frequency > 5:
                trend = "increasing"
            elif frequency < 1:
                trend = "decreasing"

        # Anomaly detection
        anomaly = None
        if frequency > 5:
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
            "anomaly": anomaly,
        }

    async def get_platform_analytics(self) -> dict:
        """Get platform-wide analytics."""
        from sqlalchemy import func, select

        from app.models.check_result import CheckResult

        result = await self.db.execute(select(func.count(CheckResult.id)))
        total_checks = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(CheckResult.id))
            .where(CheckResult.status == "changed")
        )
        total_changes = result.scalar() or 0

        return {
            "total_checks": total_checks,
            "total_changes": total_changes,
            "change_rate": round(total_changes / max(total_checks, 1), 4),
        }
