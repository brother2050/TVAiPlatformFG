"""Tests for export endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_episode_not_found(client: AsyncClient):
    """Test exporting non-existent episode."""
    response = await client.post(
        "/api/episodes/nonexistent-id/export",
        json={"resolution": "1920x1080", "fps": 30, "codec": "libx264", "quality": 23}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_export_empty(client: AsyncClient):
    """Test batch export with no episodes."""
    response = await client.post(
        "/api/export/batch",
        json={"episode_ids": [], "settings": {"resolution": "1920x1080"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") != 0 or data.get("message", "").lower().find("no episode") >= 0


@pytest.mark.asyncio
async def test_get_export_status_not_found(client: AsyncClient):
    """Test getting status for non-existent export."""
    response = await client.get("/api/exports/nonexistent-export-id")
    assert response.status_code == 200
    data = response.json()
    assert data.get("data", {}).get("status") == "not_found"


@pytest.mark.asyncio
async def test_list_exports(client: AsyncClient):
    """Test listing exports."""
    response = await client.get("/api/exports")
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0
    assert "exports" in data.get("data", {})


@pytest.mark.asyncio
async def test_delete_export_not_found(client: AsyncClient):
    """Test deleting non-existent export."""
    response = await client.delete("/api/exports/nonexistent-export-id")
    assert response.status_code == 200
    data = response.json()
    # Should return error for non-existent file
    assert data.get("code") != 0 or "not found" in data.get("message", "").lower()


@pytest.mark.asyncio
async def test_storage_usage_not_found(client: AsyncClient):
    """Test getting storage usage for non-existent episode."""
    response = await client.get("/api/episodes/nonexistent-id/storage-usage")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_storage_summary(client: AsyncClient):
    """Test getting storage summary."""
    response = await client.get("/api/storage/summary")
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0
    assert "total" in data.get("data", {})
    assert "used" in data.get("data", {})
    assert "percent" in data.get("data", {})
