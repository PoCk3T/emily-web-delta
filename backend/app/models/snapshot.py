"""Snapshot model for page content snapshots."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Snapshot(Base):
    """A snapshot of a monitored URL's content at a point in time."""

    __tablename__ = "url_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ok")
    snapshot_size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    url: Mapped["Url"] = relationship(
        "Url", back_populates="snapshots", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Snapshot(id={self.id}, url_id={self.url_id})>"


# Forward references
from app.models.url import Url  # noqa: E402
