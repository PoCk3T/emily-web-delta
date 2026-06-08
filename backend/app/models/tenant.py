"""Tenant model for multi-tenancy."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
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
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", lazy="selectin",
        primaryjoin="foreign(users.c.tenant_id) == tenants.c.id",
    )
    urls: Mapped[list["Url"]] = relationship(
        "Url", back_populates="tenant", lazy="select"
    )
    notification_rules: Mapped[list["NotificationRule"]] = relationship(
        "NotificationRule", back_populates="tenant", lazy="select"
    )
    firecrawl_monitors: Mapped[list["FirecrawlMonitor"]] = relationship(
        "FirecrawlMonitor", back_populates="tenant", lazy="select"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="tenant", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"


# Forward references
from app.models.api_key import ApiKey  # noqa: E402
from app.models.firecrawl_monitor import FirecrawlMonitor  # noqa: E402
from app.models.notification import NotificationRule  # noqa: E402
from app.models.url import Url  # noqa: E402
from app.models.user import User  # noqa: E402
