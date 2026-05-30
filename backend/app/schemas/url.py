"""URL schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class UrlCreate(BaseModel):
    """Schema for creating a new monitored URL."""

    url: HttpUrl
    name: str | None = Field(default=None, max_length=255)
    interval_seconds: int = Field(default=300, ge=60, le=86400)
    enabled: bool = True
    backend: str = Field(default="firecrawl", pattern="^(firecrawl|selfhosted)$")
    headers: dict | None = None
    cookies: dict | None = None
    js_required: bool = False
    max_retries: int = Field(default=3, ge=0, le=10)
    user_agent: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    firecrawl_config: dict | None = None


class UrlUpdate(BaseModel):
    """Schema for updating a monitored URL."""

    url: HttpUrl | None = None
    name: str | None = Field(default=None, max_length=255)
    interval_seconds: int | None = Field(default=None, ge=60, le=86400)
    enabled: bool | None = None
    backend: str | None = Field(default=None, pattern="^(firecrawl|selfhosted)$")
    headers: dict | None = None
    cookies: dict | None = None
    js_required: bool | None = None
    max_retries: int | None = Field(default=None, ge=0, le=10)
    user_agent: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    firecrawl_config: dict | None = None


class UrlEnable(BaseModel):
    """Schema for enabling a URL."""

    enabled: bool = True


class UrlCheckNow(BaseModel):
    """Schema for triggering an immediate check."""

    pass


class UrlOut(BaseModel):
    """Schema for URL response."""

    id: UUID
    tenant_id: UUID
    name: str | None = None
    url: str
    backend: str
    interval_seconds: int
    enabled: bool
    state: str
    last_checked: datetime | None = None
    last_hash: str | None = None
    next_check: datetime | None = None
    headers: dict | None = None
    cookies: dict | None = None
    js_required: bool
    max_retries: int
    user_agent: str | None = None
    tags: list[str] | None = None
    firecrawl_config: dict | None = None
    failure_consecutive_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UrlListResponse(BaseModel):
    """Paginated URL list response."""

    data: list[UrlOut]
    pagination: dict = Field(
        default_factory=lambda: {
            "page": 1,
            "per_page": 20,
            "total": 0,
            "total_pages": 0,
        }
    )


class UrlHealth(BaseModel):
    """URL health status response."""

    url_id: UUID
    state: str
    last_checked: datetime | None = None
    consecutive_failures: int
    last_error: str | None = None
    last_status_code: int | None = None

    model_config = {"from_attributes": True}
