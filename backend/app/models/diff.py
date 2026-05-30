"""Diff model for change detection results."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DiffType:
    """Valid diff types."""

    UNIFIED = "unified"
    SEMANTIC = "semantic"
    JSON = "json"


class Diff(Base):
    """A diff between two snapshots of a monitored URL."""

    __tablename__ = "url_diffs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_from_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("url_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    snapshot_to_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("url_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    diff_type: Mapped[str] = mapped_column(
        String(20), default=DiffType.UNIFIED, nullable=False
    )
    diff_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diff_size: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    url: Mapped["Url"] = relationship(
        "Url", back_populates="diffs", lazy="selectin"
    )
    snapshot_from: Mapped["Snapshot | None"] = relationship(
        "Snapshot", foreign_keys=[snapshot_from_id], lazy="selectin"
    )
    snapshot_to: Mapped["Snapshot"] = relationship(
        "Snapshot", foreign_keys=[snapshot_to_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Diff(id={self.id}, url_id={self.url_id})>"


# Forward references
from app.models.url import Url  # noqa: E402
from app.models.snapshot import Snapshot  # noqa: E402
