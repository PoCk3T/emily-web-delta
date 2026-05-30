"""Snapshot schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SnapshotOut(BaseModel):
    """Schema for snapshot response."""

    id: UUID
    url_id: UUID
    content_hash: str
    content: str | None = None
    extracted_text: str | None = None
    content_type: str | None = None
    status: str
    snapshot_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotListResponse(BaseModel):
    """Paginated snapshot list response."""

    data: list[SnapshotOut]
    pagination: dict = Field(
        default_factory=lambda: {
            "page": 1,
            "per_page": 20,
            "total": 0,
            "total_pages": 0,
        }
    )
