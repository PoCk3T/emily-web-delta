"""Tenant model for multi-tenancy."""

import uuid
from datetime import datetime, timezone

from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, and_
from sqlalchemy.orm import ColumnProperty, foreign
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tenant(Base):
    """Multi-tenant organization."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    max_urls: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="tenant", lazy="selectin",
    )
    urls: Mapped[List["Url"]] = relationship(
        "Url", back_populates="tenant", lazy="select"
    )
    notification_rules: Mapped[List["NotificationRule"]] = relationship(
        "NotificationRule", back_populates="tenant", lazy="select"
    )
    firecrawl_monitors: Mapped[List["FirecrawlMonitor"]] = relationship(
        "FirecrawlMonitor", back_populates="tenant", lazy="select"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey", back_populates="tenant", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"


# Forward references
from app.models.user import User  # noqa: E402
from app.models.url import Url  # noqa: E402
from app.models.notification import NotificationRule  # noqa: E402
from app.models.firecrawl_monitor import FirecrawlMonitor  # noqa: E402
from app.models.api_key import ApiKey  # noqa: E402

# Configure remote_side after all models are loaded (avoids circular import).
Tenant.owner.property.remote_side = {User.__table__.c.tenant_id}  # noqa: E402
