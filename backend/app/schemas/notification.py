"""Notification schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationRuleCreate(BaseModel):
    """Schema for creating a notification rule."""

    type: str = Field(default="email", pattern="^(email|webhook|slack|telegram|discord)$")
    channel: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    url_id: UUID | None = None
    min_diff_size: int = Field(default=0, ge=0)
    significant_only: bool = False
    cooldown_seconds: int = Field(default=300, ge=0)
    max_notifications_per_day: int = Field(default=50, ge=1)
    config: dict | None = None


class NotificationRuleUpdate(BaseModel):
    """Schema for updating a notification rule."""

    type: str | None = Field(default=None, pattern="^(email|webhook|slack|telegram|discord)$")
    channel: str | None = Field(default=None, min_length=1, max_length=500)
    enabled: bool | None = None
    url_id: UUID | None = None
    min_diff_size: int | None = Field(default=None, ge=0)
    significant_only: bool | None = None
    cooldown_seconds: int | None = Field(default=None, ge=0)
    max_notifications_per_day: int | None = Field(default=None, ge=1)
    config: dict | None = None


class NotificationRuleOut(BaseModel):
    """Schema for notification rule response."""

    id: UUID
    tenant_id: UUID
    url_id: UUID | None = None
    type: str
    channel: str
    enabled: bool
    min_diff_size: int
    significant_only: bool
    cooldown_seconds: int
    max_notifications_per_day: int
    last_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationTestResponse(BaseModel):
    """Response for testing a notification."""

    success: bool
    message: str
    channel: str
