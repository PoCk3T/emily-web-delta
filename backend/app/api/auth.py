"""Authentication API routes."""


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_session
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/auth/register", response_model=dict)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_session)):
    """Register a new user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create tenant for the user
    tenant = Tenant(
        name=request.name,
        owner=user,
        is_active=True,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat(),
    }


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_session)):
    """Login and get JWT tokens."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
    }


@router.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Invalidate session (stateless - token expires naturally)."""
    return {"message": "Logged out successfully"}


@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": request.refresh_token,
    }


@router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset (sends email with reset link)."""
    # In production: send email with reset token
    # For now, just acknowledge
    return {"message": "Password reset link sent (if account exists)"}


@router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm, db: AsyncSession = Depends(get_session)):
    """Reset password with token."""
    payload = decode_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )

    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = hash_password(request.new_password)
    await db.commit()

    return {"message": "Password reset successful"}


@router.get("/auth/me")
async def get_me(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)):
    """Get current user profile."""
    from uuid import UUID

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == UUID(payload.get("sub"))))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }
