"""Notification rule model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class NotificationType:
    """Valid notification types."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TELEGRAM = "telegram"
    DISCORD = "discord"


class NotificationRule(Base):
    """Notification rule configuration for a tenant."""

    __tablename__ = "notification_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(20), default=NotificationType.EMAIL, nullable=False
    )
    channel: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    min_diff_size: Mapped[int] = mapped_column(Integer, default=0)
    significant_only: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=300)
    max_notifications_per_day: Mapped[int] = mapped_column(
        Integer, default=50
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="notification_rules", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<NotificationRule(id={self.id}, type={self.type}, channel={self.channel})>"


# Forward reference
from app.models.tenant import Tenant  # noqa: E402
