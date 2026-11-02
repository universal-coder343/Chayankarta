"""
Tests for the /health endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    """Health endpoint should return 200 with status info."""
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_db_connected(async_client):
    """When DB is mocked and responding, health should report 'connected'."""
    response = await async_client.get("/health")
    data = response.json()
    assert data["db"] == "connected"
    assert data["status"] == "ok"
