"""User and authentication schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    tenant_name: str | None = Field(default=None, description="Optional custom tenant name")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until expiration")


class TokenRefresh(BaseModel):
    """Schema for refreshing a JWT token."""

    refresh_token: str


class UserOut(BaseModel):
    """Schema for user response (excluding sensitive data)."""

    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    is_active: bool | None = None
    is_superuser: bool | None = None


class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset."""

    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for resetting a password with a token."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class MeResponse(BaseModel):
    """Response for the current user profile."""

    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    tenant_id: UUID | None = None
    tenant_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
