"""URL management API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.url_validator import validate_url
from app.db.session import get_session
from app.models.url import Url

router = APIRouter()


class UrlCreateRequest(BaseModel):
    name: str
    url: str
    interval_seconds: int = Field(default=3600, ge=60, le=86400)
    enabled: bool = True
    backend: str = "firecrawl"
    headers: Optional[dict] = None
    cookies: Optional[dict] = None
    js_required: bool = False
    max_retries: int = 3
    user_agent: Optional[str] = None
    goal: Optional[str] = None
    tags: list[str] = []


class UrlUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval_seconds: Optional[int] = None
    enabled: Optional[bool] = None
    backend: Optional[str] = None
    headers: Optional[dict] = None
    cookies: Optional[dict] = None
    js_required: Optional[bool] = None
    max_retries: Optional[int] = None
    user_agent: Optional[str] = None
    goal: Optional[str] = None
    tags: Optional[list[str]] = None


class UrlResponse(BaseModel):
    id: str
    name: str
    url: str
    interval_seconds: int
    enabled: bool
    backend: str
    last_checked: Optional[str] = None
    last_hash: Optional[str] = None
    next_check: Optional[str] = None
    tags: list[str]
    status: str = "active"
    created_at: str
    snapshot_count: int = 0


@router.post("/urls", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_url(request: UrlCreateRequest, db: AsyncSession = Depends(get_session)):
    """Create a new URL to monitor."""
    valid, error = validate_url(request.url)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Check for duplicate
    result = await db.execute(select(Url).where(Url.url == request.url))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="URL already being monitored",
        )

    url = Url(
        name=request.name,
        url=request.url,
        interval_seconds=request.interval_seconds,
        enabled=request.enabled,
        backend=request.backend,
        headers=request.headers,
        cookies=request.cookies,
        js_required=request.js_required,
        max_retries=request.max_retries,
        user_agent=request.user_agent,
        goal=request.goal,
        tags=request.tags,
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)

    return UrlResponse(
        id=str(url.id),
        name=url.name,
        url=url.url,
        interval_seconds=url.interval_seconds,
        enabled=url.enabled,
        backend=url.backend,
        last_checked=url.last_checked.isoformat() if url.last_checked else None,
        last_hash=url.last_hash,
        next_check=url.next_check.isoformat() if url.next_check else None,
        tags=url.tags or [],
        created_at=url.created_at.isoformat(),
    )


@router.get("/urls")
async def list_urls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    backend: Optional[str] = None,
    enabled: Optional[bool] = None,
    tag: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """List all URLs with pagination and filtering."""
    query = select(Url).options(selectinload(Url.snapshots))

    if backend:
        query = query.where(Url.backend == backend)
    if enabled is not None:
        query = query.where(Url.enabled == enabled)
    if tag:
        query = query.where(Url.tags.contains([tag]))

    # Count total
    count_result = await db.execute(select(Url).where(query.whereclause if hasattr(query, 'whereclause') else True))
    total = len(count_result.scalars().all())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Url.created_at.desc())
    result = await db.execute(query)
    urls = result.scalars().all()

    return {
        "data": [
            UrlResponse(
                id=str(u.id),
                name=u.name,
                url=u.url,
                interval_seconds=u.interval_seconds,
                enabled=u.enabled,
                backend=u.backend,
                last_checked=u.last_checked.isoformat() if u.last_checked else None,
                last_hash=u.last_hash,
                next_check=u.next_check.isoformat() if u.next_check else None,
                tags=u.tags or [],
                created_at=u.created_at.isoformat(),
                snapshot_count=u.snapshot_count or 0,
            )
            for u in urls
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }


@router.get("/urls/{url_id}", response_model=UrlResponse)
async def get_url(url_id: str, db: AsyncSession = Depends(get_session)):
    """Get URL details."""
    from uuid import UUID
    result = await db.execute(select(Url).options(selectinload(Url.snapshots)).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    return UrlResponse(
        id=str(url.id),
        name=url.name,
        url=url.url,
        interval_seconds=url.interval_seconds,
        enabled=url.enabled,
        backend=url.backend,
        last_checked=url.last_checked.isoformat() if url.last_checked else None,
        last_hash=url.last_hash,
        next_check=url.next_check.isoformat() if url.next_check else None,
        tags=url.tags or [],
        created_at=url.created_at.isoformat(),
        snapshot_count=url.snapshot_count or 0,
    )


@router.put("/urls/{url_id}", response_model=UrlResponse)
async def update_url(url_id: str, request: UrlUpdateRequest, db: AsyncSession = Depends(get_session)):
    """Update URL configuration."""
    from uuid import UUID
    result = await db.execute(select(Url).options(selectinload(Url.snapshots)).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    if request.url:
        valid, error = validate_url(request.url)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    for field_name, value in request.model_dump(exclude_unset=True).items():
        setattr(url, field_name, value)

    await db.commit()
    await db.refresh(url)

    return UrlResponse(
        id=str(url.id),
        name=url.name,
        url=url.url,
        interval_seconds=url.interval_seconds,
        enabled=url.enabled,
        backend=url.backend,
        last_checked=url.last_checked.isoformat() if url.last_checked else None,
        last_hash=url.last_hash,
        next_check=url.next_check.isoformat() if url.next_check else None,
        tags=url.tags or [],
        created_at=url.created_at.isoformat(),
        snapshot_count=url.snapshot_count or 0,
    )


@router.delete("/urls/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(url_id: str, db: AsyncSession = Depends(get_session)):
    """Delete a URL."""
    from uuid import UUID
    result = await db.execute(select(Url).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    await db.delete(url)
    await db.commit()


@router.patch("/urls/{url_id}/enable")
async def enable_url(url_id: str, db: AsyncSession = Depends(get_session)):
    """Enable URL monitoring."""
    from uuid import UUID
    result = await db.execute(select(Url).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    url.enabled = True
    await db.commit()
    return {"enabled": True}


@router.patch("/urls/{url_id}/disable")
async def disable_url(url_id: str, db: AsyncSession = Depends(get_session)):
    """Disable URL monitoring."""
    from uuid import UUID
    result = await db.execute(select(Url).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    url.enabled = False
    await db.commit()
    return {"enabled": False}


@router.post("/urls/{url_id}/check-now")
async def check_now(url_id: str, db: AsyncSession = Depends(get_session)):
    """Trigger an immediate check for a URL."""
    from uuid import UUID
    result = await db.execute(select(Url).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    url.last_checked = None
    await db.commit()
    return {"message": "Check queued", "url_id": str(url.id)}


@router.get("/urls/{url_id}/health")
async def url_health(url_id: str, db: AsyncSession = Depends(get_session)):
    """Get URL health status."""
    from uuid import UUID
    result = await db.execute(select(Url).where(Url.id == UUID(url_id)))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    return {
        "url_id": str(url.id),
        "url": url.url,
        "enabled": url.enabled,
        "last_checked": url.last_checked.isoformat() if url.last_checked else None,
        "backend": url.backend,
        "status": "active" if url.enabled else "disabled",
    }
