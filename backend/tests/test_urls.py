"""Tests for URL CRUD."""

from httpx import AsyncClient
from sqlalchemy import select


async def test_create_url(client: AsyncClient):
    """Test creating a URL."""
    response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "interval_seconds": 3600,
            "enabled": True,
            "backend": "firecrawl",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test URL"
    assert data["url"] == "https://example.com"
    assert data["backend"] == "firecrawl"


async def test_list_urls(client: AsyncClient):
    """Test listing URLs."""
    # Create a URL first
    await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "interval_seconds": 3600,
        },
    )

    response = await client.get("/api/v1/urls")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) >= 1


async def test_get_url(client: AsyncClient):
    """Test getting a single URL."""
    # Create a URL first
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "interval_seconds": 3600,
        },
    )
    url_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/urls/{url_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == url_id


async def test_update_url(client: AsyncClient):
    """Test updating a URL."""
    # Create a URL first
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "interval_seconds": 3600,
        },
    )
    url_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/urls/{url_id}",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


async def test_delete_url(client: AsyncClient):
    """Test deleting a URL."""
    # Create a URL first
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "interval_seconds": 3600,
        },
    )
    url_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/urls/{url_id}")
    assert response.status_code == 204


async def test_enable_url(client: AsyncClient):
    """Test enabling a URL."""
    # Create a disabled URL
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "enabled": False,
        },
    )
    url_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/urls/{url_id}/enable")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


async def test_disable_url(client: AsyncClient):
    """Test disabling a URL."""
    response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
            "enabled": True,
        },
    )
    url_id = response.json()["id"]

    response = await client.patch(f"/api/v1/urls/{url_id}/disable")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


async def test_check_now(client: AsyncClient):
    """Test triggering an immediate check."""
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
        },
    )
    url_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/urls/{url_id}/check-now")
    assert response.status_code == 200
    assert response.json()["message"] == "Check queued"


async def test_url_health(client: AsyncClient):
    """Test URL health endpoint."""
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Test URL",
            "url": "https://example.com",
        },
    )
    url_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/urls/{url_id}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://example.com"


async def test_create_defaults_to_polled_backend(client: AsyncClient):
    """Omitting `backend` must yield a backend the poller actually services."""
    response = await client.post(
        "/api/v1/urls",
        json={"name": "Defaults", "url": "https://example.com/defaults"},
    )
    assert response.status_code == 201
    assert response.json()["backend"] == "selfhosted"


async def test_create_schedules_first_check(client: AsyncClient):
    """A new URL must be schedulable immediately, not left unscheduled."""
    response = await client.post(
        "/api/v1/urls",
        json={"name": "Scheduled", "url": "https://example.com/scheduled"},
    )
    assert response.status_code == 201
    assert response.json()["next_check"] is not None


async def test_toggle_endpoint_disables_and_enables(client: AsyncClient):
    """The web UI drives enable/disable through PATCH /toggle."""
    create_response = await client.post(
        "/api/v1/urls",
        json={"name": "Toggle", "url": "https://example.com/toggle"},
    )
    url_id = create_response.json()["id"]

    off = await client.patch(f"/api/v1/urls/{url_id}/toggle", json={"enabled": False})
    assert off.status_code == 200
    assert off.json()["enabled"] is False
    assert off.json()["status"] == "disabled"

    on = await client.patch(f"/api/v1/urls/{url_id}/toggle", json={"enabled": True})
    assert on.status_code == 200
    assert on.json()["enabled"] is True
    assert on.json()["status"] == "active"


async def test_toggle_unknown_url_returns_404(client: AsyncClient):
    response = await client.patch(
        "/api/v1/urls/00000000-0000-0000-0000-000000000000/toggle",
        json={"enabled": True},
    )
    assert response.status_code == 404


async def test_check_alias_matches_check_now(client: AsyncClient):
    """The frontend calls /check; it must resolve like /check-now."""
    create_response = await client.post(
        "/api/v1/urls",
        json={"name": "Alias", "url": "https://example.com/alias"},
    )
    url_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/urls/{url_id}/check")
    assert response.status_code == 200
    assert response.json()["message"] == "Check queued"


async def test_check_now_marks_url_due(client: AsyncClient):
    """A manual check must make the URL due even if Celery never runs."""
    create_response = await client.post(
        "/api/v1/urls",
        json={
            "name": "Due",
            "url": "https://example.com/due",
            "interval_seconds": 86400,
        },
    )
    url_id = create_response.json()["id"]

    await client.post(f"/api/v1/urls/{url_id}/check-now")

    detail = await client.get(f"/api/v1/urls/{url_id}")
    assert detail.json()["next_check"] is not None


async def test_created_url_is_attached_to_tenant(client: AsyncClient, db_session):
    """URLs must join the existing tenant so tenant-wide rules apply to them."""
    from app.models.tenant import Tenant
    from app.models.url import Url

    tenant = Tenant(name="Emily", is_active=True)
    db_session.add(tenant)
    await db_session.commit()

    response = await client.post(
        "/api/v1/urls",
        json={"name": "Tenant", "url": "https://example.com/tenant"},
    )
    assert response.status_code == 201

    row = (
        await db_session.execute(
            select(Url).where(Url.url == "https://example.com/tenant")
        )
    ).scalar_one()
    assert row.tenant_id == tenant.id


async def test_duplicate_url_is_rejected(client: AsyncClient):
    payload = {"name": "Dup", "url": "https://example.com/dup"}
    first = await client.post("/api/v1/urls", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/urls", json=payload)
    assert second.status_code == 409
