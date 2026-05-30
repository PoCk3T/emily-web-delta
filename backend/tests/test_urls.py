"""Tests for URL CRUD."""

from httpx import AsyncClient


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
