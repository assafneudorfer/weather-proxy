import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient):
    """Test health check returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["redis_connected"] is True


@pytest.mark.asyncio
async def test_health_check_has_request_id(client: AsyncClient):
    """Test health check response includes correlation ID."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
