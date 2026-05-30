"""Notification service layer."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Service layer for sending notifications."""

    def __init__(self, db_session):
        self.db = db_session

    async def send_notification(
        self,
        rule_id: str,
        message: str,
        context: Optional[dict] = None,
    ) -> bool:
        """Send a notification based on a rule."""
        from app.models.notification import NotificationRule

        result = await self.db.execute(
            self._select_rule(rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule or not rule.enabled:
            return False

        try:
            if rule.type == "email":
                return await self._send_email(rule, message)
            elif rule.type == "webhook":
                return await self._send_webhook(rule, message, context)
            elif rule.type == "slack":
                return await self._send_slack(rule, message)
            elif rule.type == "telegram":
                return await self._send_telegram(rule, message)
            elif rule.type == "discord":
                return await self._send_discord(rule, message)
            else:
                logger.warning(f"Unknown notification type: {rule.type}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def _send_email(self, rule, message: str) -> bool:
        """Send email notification."""
        # In production: use SMTP or SES
        logger.info(f"Sending email to {rule.channel}: {message}")
        return True

    async def _send_webhook(self, rule, message: str, context: Optional[dict]) -> bool:
        """Send webhook notification."""
        # In production: use httpx to POST to webhook URL
        logger.info(f"Sending webhook to {rule.channel}")
        return True

    async def _send_slack(self, rule, message: str) -> bool:
        """Send Slack notification."""
        logger.info(f"Sending Slack message to {rule.channel}")
        return True

    async def _send_telegram(self, rule, message: str) -> bool:
        """Send Telegram notification."""
        logger.info(f"Sending Telegram message to {rule.channel}")
        return True

    async def _send_discord(self, rule, message: str) -> bool:
        """Send Discord notification."""
        logger.info(f"Sending Discord message to {rule.channel}")
        return True

    def _select_rule(self, rule_id: str):
        """Create a select statement for a notification rule."""
        from sqlalchemy import select
        from app.models.notification import NotificationRule

        return select(NotificationRule).where(NotificationRule.id == rule_id)
