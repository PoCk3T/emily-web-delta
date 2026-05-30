"""Diff schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiffOut(BaseModel):
    """Schema for diff response."""

    id: UUID
    url_id: UUID
    snapshot_from_id: UUID | None = None
    snapshot_to_id: UUID
    diff_type: str
    diff_content: str | None = None
    diff_json: dict | None = None
    diff_size: int
    lines_added: int
    lines_removed: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DiffListResponse(BaseModel):
    """Paginated diff list response."""

    data: list[DiffOut]
    pagination: dict = Field(
        default_factory=lambda: {
            "page": 1,
            "per_page": 20,
            "total": 0,
            "total_pages": 0,
        }
    )


class DiffRendered(BaseModel):
    """Rendered diff response."""

    html: str
    diff_type: str
    lines_added: int
    lines_removed: int


class DiffDownload(BaseModel):
    """Downloadable diff response."""

    filename: str
    content_type: str
    content: str
