"""URL management API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.url_validator import validate_url
from app.db.session import get_session
from app.models.tenant import Tenant
from app.models.url import Url

router = APIRouter()

# Only "selfhosted" URLs are picked up by the Celery poller
# (see app/workers/polling.py::async_poll_urls).
DEFAULT_BACKEND = "selfhosted"


async def _default_tenant_id(db: AsyncSession) -> UUID | None:
    """Resolve the tenant new URLs should belong to.

    The deployment is effectively single-tenant, but leaving tenant_id NULL
    orphans the row from the tenant's notification rules. Attach to the
    first (oldest) tenant when one exists.
    """
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.asc()).limit(1))
    tenant = result.scalar_one_or_none()
    return tenant.id if tenant else None


class UrlCreateRequest(BaseModel):
    name: str
    url: str
    interval_seconds: int = Field(default=3600, ge=60, le=86400)
    enabled: bool = True
    # Defaults to "selfhosted": it is the only backend the Celery poller
    # actually services. A URL created as "firecrawl" is never polled because
    # no Firecrawl monitor is provisioned anywhere in the codebase.
    backend: str = DEFAULT_BACKEND
    headers: dict | None = None
    cookies: dict | None = None
    js_required: bool = False
    max_retries: int = 3
    user_agent: str | None = None
    goal: str | None = None
    tags: list[str] = []


class UrlUpdateRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    interval_seconds: int | None = None
    enabled: bool | None = None
    backend: str | None = None
    headers: dict | None = None
    cookies: dict | None = None
    js_required: bool | None = None
    max_retries: int | None = None
    user_agent: str | None = None
    goal: str | None = None
    tags: list[str] | None = None


class UrlResponse(BaseModel):
    id: str
    name: str
    url: str
    interval_seconds: int
    enabled: bool
    backend: str
    last_checked: str | None = None
    last_hash: str | None = None
    next_check: str | None = None
    tags: list[str]
    status: str = "active"
    created_at: str
    snapshot_count: int = 0


def _to_response(url: Url, *, snapshot_count: int | None = None) -> UrlResponse:
    """Serialize a Url row.

    Centralized so every endpoint returns an identical shape — previously
    each handler rebuilt this by hand and they had already drifted apart
    (e.g. create() always reported snapshot_count as 0).
    """
    if snapshot_count is None:
        try:
            snapshot_count = url.snapshot_count or 0
        except Exception:
            # snapshots relationship not eagerly loaded on this instance.
            snapshot_count = 0

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
        status="active" if url.enabled else "disabled",
        created_at=url.created_at.isoformat(),
        snapshot_count=snapshot_count,
    )


@router.post("/urls", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_url(
    request: UrlCreateRequest, db: AsyncSession = Depends(get_session)
):
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
        tenant_id=await _default_tenant_id(db),
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
        # Schedule the first check immediately. Leaving this NULL relies on
        # the scheduler's NULL handling and delays the first poll by a full
        # interval; setting it explicitly makes new URLs verifiable at once.
        next_check=datetime.now(UTC),
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)

    return _to_response(url, snapshot_count=0)


@router.get("/urls")
async def list_urls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    backend: str | None = None,
    enabled: bool | None = None,
    tag: str | None = None,
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
    count_result = await db.execute(
        select(Url).where(query.whereclause if hasattr(query, "whereclause") else True)
    )
    total = len(count_result.scalars().all())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Url.created_at.desc())
    result = await db.execute(query)
    urls = result.scalars().all()

    return {
        "data": [_to_response(u) for u in urls],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }


@router.get("/urls/{url_id}", response_model=UrlResponse)
async def get_url(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Get URL details."""

    result = await db.execute(
        select(Url).options(selectinload(Url.snapshots)).where(Url.id == url_id)
    )
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    return _to_response(url)


@router.put("/urls/{url_id}", response_model=UrlResponse)
async def update_url(
    url_id: UUID, request: UrlUpdateRequest, db: AsyncSession = Depends(get_session)
):
    """Update URL configuration."""

    result = await db.execute(
        select(Url).options(selectinload(Url.snapshots)).where(Url.id == url_id)
    )
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    if request.url:
        valid, error = validate_url(request.url)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    for field_name, value in request.model_dump(exclude_unset=True).items():
        setattr(url, field_name, value)

    await db.commit()
    await db.refresh(url)

    return _to_response(url)


@router.delete("/urls/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Delete a URL."""

    result = await db.execute(select(Url).where(Url.id == url_id))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    await db.delete(url)
    await db.commit()


@router.patch("/urls/{url_id}/enable")
async def enable_url(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Enable URL monitoring."""

    result = await db.execute(select(Url).where(Url.id == url_id))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    url.enabled = True
    await db.commit()
    return {"enabled": True}


@router.patch("/urls/{url_id}/disable")
async def disable_url(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Disable URL monitoring."""

    result = await db.execute(select(Url).where(Url.id == url_id))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    url.enabled = False
    await db.commit()
    return {"enabled": False}


class UrlToggleRequest(BaseModel):
    enabled: bool


@router.patch("/urls/{url_id}/toggle", response_model=UrlResponse)
async def toggle_url(
    url_id: UUID,
    request: UrlToggleRequest,
    db: AsyncSession = Depends(get_session),
):
    """Enable or disable URL monitoring, returning the full updated URL.

    The web UI drives enable/disable through this single endpoint and expects
    a complete URL object back so it can refresh its cache in place.
    """

    result = await db.execute(
        select(Url).options(selectinload(Url.snapshots)).where(Url.id == url_id)
    )
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    url.enabled = request.enabled
    if request.enabled and url.next_check is None:
        # Re-enabling a never-scheduled URL should make it due immediately.
        url.next_check = datetime.now(UTC)

    await db.commit()
    await db.refresh(url)

    return _to_response(url)


@router.post("/urls/{url_id}/check-now")
@router.post("/urls/{url_id}/check")
async def check_now(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Trigger an immediate check for a URL.

    Exposed under both `/check-now` and `/check`; the web UI calls the
    latter.
    """

    result = await db.execute(select(Url).where(Url.id == url_id))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    # Mark the URL as due right now, so that even if the Celery dispatch
    # below fails the next scheduler tick will still pick it up.
    url.next_check = datetime.now(UTC)
    await db.commit()

    # Trigger immediate celery poll
    try:
        from app.workers.polling import poll_urls

        poll_urls.delay([str(url.id)])
    except Exception:
        # Fallback if celery is not running (e.g. in test env)
        pass

    return {"message": "Check queued", "url_id": str(url.id)}


@router.get("/urls/{url_id}/health")
async def url_health(url_id: UUID, db: AsyncSession = Depends(get_session)):
    """Get URL health status."""

    result = await db.execute(select(Url).where(Url.id == url_id))
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    return {
        "url_id": str(url.id),
        "url": url.url,
        "enabled": url.enabled,
        "last_checked": url.last_checked.isoformat() if url.last_checked else None,
        "backend": url.backend,
        "status": "active" if url.enabled else "disabled",
    }
