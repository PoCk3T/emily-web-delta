"""Firecrawl monitor model for mapping internal monitors to Firecrawl."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FirecrawlMonitor(Base):
    """Maps an internal URL monitor to a Firecrawl monitor."""

    __tablename__ = "firecrawl_monitors"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    firecrawl_monitor_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    firecrawl_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )
    last_check_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    last_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_credits_per_month: Mapped[int] = mapped_column(
        Integer, default=0
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
        "Tenant", back_populates="firecrawl_monitors", lazy="selectin"
    )
    url: Mapped["Url"] = relationship(
        "Url", back_populates="firecrawl_monitors", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<FirecrawlMonitor(id={self.id}, firecrawl_id={self.firecrawl_monitor_id})>"


# Forward references
from app.models.tenant import Tenant  # noqa: E402
from app.models.url import Url  # noqa: E402
