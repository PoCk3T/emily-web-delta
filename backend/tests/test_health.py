"""Tests for health endpoint."""

from httpx import AsyncClient


async def test_health(client: AsyncClient):
    """Test health endpoint returns OK."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


async def test_ready(client: AsyncClient):
    """Test readiness endpoint."""
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
