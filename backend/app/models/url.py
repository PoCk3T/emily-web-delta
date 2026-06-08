"""URL model for monitored web pages."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UrlState:
    """Valid URL states for the state machine."""

    ACTIVE = "ACTIVE"
    ERRORING = "ERRORING"
    DOWN = "DOWN"
    DELETED = "DELETED"
    UNREACHABLE = "UNREACHABLE"
    RECOVERED = "RECOVERED"


class Url(Base):
    """A URL to be monitored for changes."""

    __tablename__ = "urls"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    backend: Mapped[str] = mapped_column(
        String(20), default="firecrawl", nullable=False
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    state: Mapped[str] = mapped_column(
        String(20), default=UrlState.ACTIVE, nullable=False
    )
    last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_check: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cookies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    js_required: Mapped[bool] = mapped_column(Boolean, default=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    firecrawl_config: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_consecutive_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="urls", lazy="selectin"
    )
    snapshots: Mapped[list["Snapshot"]] = relationship(
        "Snapshot", back_populates="url", lazy="select"
    )
    diffs: Mapped[list["Diff"]] = relationship(
        "Diff", back_populates="url", lazy="select"
    )
    check_results: Mapped[list["CheckResult"]] = relationship(
        "CheckResult", back_populates="url", lazy="select"
    )
    firecrawl_monitors: Mapped[list["FirecrawlMonitor"]] = relationship(
        "FirecrawlMonitor", back_populates="url", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Url(id={self.id}, name={self.name}, url={self.url})>"

    @property
    def snapshot_count(self) -> int:
        """Count of snapshots for this URL."""
        return len(self.snapshots) if self.snapshots else 0


# Forward references

from app.models.check_result import CheckResult  # noqa: E402
from app.models.diff import Diff  # noqa: E402
from app.models.firecrawl_monitor import FirecrawlMonitor  # noqa: E402
from app.models.snapshot import Snapshot  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
