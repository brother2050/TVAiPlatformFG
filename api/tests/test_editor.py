"""Tests for editor endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_dialogue_text_empty(client: AsyncClient):
    """Test updating dialogue text with empty content."""
    response = await client.put(
        "/api/editor/dialogues/test-id/text",
        json={"text": ""}
    )
    # Should return error for empty text
    data = response.json()
    assert data.get("code") != 0 or "empty" in data.get("message", "").lower()


@pytest.mark.asyncio
async def test_regenerate_image(client: AsyncClient):
    """Test regenerating image."""
    response = await client.post("/api/editor/images/test-id/regenerate")
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0
    assert "status" in data.get("data", {})


@pytest.mark.asyncio
async def test_regenerate_voice(client: AsyncClient):
    """Test regenerating voice."""
    response = await client.post("/api/editor/voices/test-id/regenerate")
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0


@pytest.mark.asyncio
async def test_update_voice_params(client: AsyncClient):
    """Test updating voice parameters."""
    response = await client.put(
        "/api/editor/voices/test-id/params",
        json={
            "speed": 1.0,
            "pitch": 0,
            "volume": 80,
            "auto_apply": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0


@pytest.mark.asyncio
async def test_update_subtitle_text(client: AsyncClient):
    """Test updating subtitle text."""
    response = await client.put(
        "/api/editor/subtitles/test-id/text",
        json={"text": "Test subtitle"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_subtitle_timing(client: AsyncClient):
    """Test updating subtitle timing."""
    response = await client.put(
        "/api/editor/subtitles/test-id/timing",
        json={"start_time": 0.5, "end_time": 3.0}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_trim_video(client: AsyncClient):
    """Test trimming video."""
    response = await client.put(
        "/api/editor/videos/test-id/trim",
        json={"start": 0, "end": 30}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_transition(client: AsyncClient):
    """Test updating video transition."""
    response = await client.put(
        "/api/editor/videos/test-id/transition",
        json={"transition": "fade"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_bgm_data_not_found(client: AsyncClient):
    """Test getting BGM data for non-existent episode."""
    response = await client.get("/api/editor/episodes/nonexistent-id/bgm")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_sfx_from_library(client: AsyncClient):
    """Test adding SFX from library."""
    response = await client.post(
        "/api/editor/episodes/test-id/sfx/library",
        json={"name": "door_open", "category": "foley"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("code") == 0
    assert data.get("data", {}).get("source") == "library"


@pytest.mark.asyncio
async def test_update_mix_levels(client: AsyncClient):
    """Test updating mix levels."""
    response = await client.put(
        "/api/editor/episodes/test-id/mix",
        json={
            "bgm": 60,
            "voice": 80,
            "ambient": 30,
            "sfx": 50
        }
    )
    assert response.status_code == 200
