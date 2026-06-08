"""Check result model for tracking URL check outcomes."""

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


class CheckResult(Base):
    """Records the result of a URL check (from Firecrawl or self-hosted)."""

    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    backend: Mapped[str] = mapped_column(
        String(20), default="firecrawl", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="completed", nullable=False
    )
    is_meaningful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    judgment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diff_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diff_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_consecutive_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    state: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    url: Mapped["Url"] = relationship(
        "Url", back_populates="check_results", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<CheckResult(id={self.id}, url_id={self.url_id}, status={self.status})>"


# Forward reference
from app.models.url import Url  # noqa: E402
