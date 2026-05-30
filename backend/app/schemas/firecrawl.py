"""Firecrawl schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FirecrawlMonitorCreate(BaseModel):
    """Schema for creating a Firecrawl monitor."""

    url_id: UUID
    firecrawl_config: dict = Field(default_factory=dict)
    interval_seconds: int = Field(default=300, ge=60, le=86400)


class FirecrawlMonitorOut(BaseModel):
    """Schema for Firecrawl monitor response."""

    id: UUID
    tenant_id: UUID
    url_id: UUID
    firecrawl_monitor_id: str
    firecrawl_config: dict
    status: str
    last_check_id: str | None = None
    last_check_at: datetime | None = None
    estimated_credits_per_month: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FirecrawlWebhookPayload(BaseModel):
    """Schema for Firecrawl webhook payloads."""

    type: str  # "monitor.page" or "monitor.check.completed"
    data: list[dict]


class FirecrawlCheckResultOut(BaseModel):
    """Schema for check result from Firecrawl."""

    id: UUID
    url_id: UUID
    check_id: str | None = None
    backend: str
    status: str
    is_meaningful: bool | None = None
    judgment: dict | None = None
    diff_size: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
