"""Tests for production endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_produce_episode_not_found(client: AsyncClient):
    """Test producing non-existent episode returns 404."""
    response = await client.post("/api/episodes/nonexistent-id/produce")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_produce_validation(client: AsyncClient):
    """Test batch produce with invalid stages."""
    response = await client.post(
        "/api/episodes/test-id/produce/batch",
        json={"stages": ["invalid_stage"]}
    )
    assert response.status_code == 200
    data = response.json()
    # Should return error for invalid stages
    assert data.get("code") != 0 or "invalid" in data.get("message", "").lower()


@pytest.mark.asyncio
async def test_get_progress_not_found(client: AsyncClient):
    """Test getting progress for non-existent episode."""
    response = await client.get("/api/episodes/nonexistent-id/progress")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_keyframe_not_found(client: AsyncClient):
    """Test regenerating keyframe for non-existent shot."""
    response = await client.post("/api/shots/nonexistent-shot/regenerate-keyframe")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_voice_not_found(client: AsyncClient):
    """Test regenerating voice for non-existent dialogue."""
    response = await client.post("/api/dialogues/nonexistent-dialogue/regenerate-voice")
    assert response.status_code == 404
