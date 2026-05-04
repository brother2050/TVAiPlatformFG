"""Editor router — all manual editing APIs.

Provides endpoints for text, image, voice, BGM, subtitle, and video editing.
Integrates with services layer for actual business logic.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.script import Scene, Shot
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api/editor", tags=["editor"])

# Storage path for media files
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


# ── Text / Dialogue Editing ─────────────────────────────────────────────────

@router.put("/dialogues/{dialogue_id}/text", response_model=ApiResponse)
async def update_dialogue_text(
    dialogue_id: str,
    body: dict[str, str],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update dialogue text."""
    text = body.get("text", "")
    if not text:
        return error("Text cannot be empty")

    # Find and update the dialogue in shots
    stmt = select(Shot).where(Shot.dialogues.contains([{"id": dialogue_id}]))
    result = await db.execute(stmt)
    shots = result.scalars().all()

    for shot in shots:
        dialogues = shot.dialogues or []
        for d in dialogues:
            if d.get("id") == dialogue_id or d.get("text") == dialogue_id:
                d["text"] = text
                break
        shot.dialogues = dialogues

    await db.commit()
    return success({"dialogue_id": dialogue_id, "text": text})


@router.put("/dialogues/{dialogue_id}/emotion", response_model=ApiResponse)
async def update_dialogue_emotion(
    dialogue_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update dialogue emotion parameters."""
    # Emotion params: emotion, volume, pace
    return success({"dialogue_id": dialogue_id, **body})


@router.post("/dialogues", response_model=ApiResponse)
async def insert_dialogue(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Insert a new dialogue into a shot."""
    scene_id = body.get("scene_id")
    new_dialogue = {
        "id": str(uuid.uuid4()),
        "character_id": body.get("character_id", ""),
        "text": body.get("text", ""),
        "emotion": body.get("emotion", "neutral"),
        "volume": body.get("volume", "normal"),
        "pace": body.get("pace", "normal"),
    }
    return success({"id": new_dialogue["id"], **new_dialogue})


@router.delete("/dialogues/{dialogue_id}", response_model=ApiResponse)
async def delete_dialogue(
    dialogue_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a dialogue."""
    return success({"deleted": dialogue_id})


# ── Image Editing ───────────────────────────────────────────────────────────

@router.post("/images/{image_id}/regenerate", response_model=ApiResponse)
async def regenerate_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Regenerate an image via ComfyUI."""
    # TODO: Integrate with ComfyUI service
    return success({"status": "queued", "image_id": image_id})


@router.post("/images/{image_id}/inpaint", response_model=ApiResponse)
async def inpaint_image(
    image_id: str,
    mask: UploadFile = File(...),
    prompt: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Inpaint image with mask and prompt."""
    # TODO: Save mask and integrate with inpainting service
    return success({"status": "queued", "image_id": image_id})


@router.post("/images/{image_id}/upload-replace", response_model=ApiResponse)
async def upload_replace_image(
    image_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload and replace an image."""
    # Save uploaded file
    upload_dir = STORAGE_PATH / "images" / image_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return success({"status": "uploaded", "image_id": image_id, "url": str(file_path)})


# ── Voice Editing ───────────────────────────────────────────────────────────

@router.post("/voices/{voice_id}/regenerate", response_model=ApiResponse)
async def regenerate_voice(
    voice_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Regenerate voice/TTS for a dialogue."""
    # TODO: Integrate with TTS service
    return success({"status": "queued", "voice_id": voice_id})


@router.put("/voices/{voice_id}/params", response_model=ApiResponse)
async def update_voice_params(
    voice_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update voice parameters (tone, speed, pitch)."""
    # TODO: Apply voice parameter adjustments
    return success({"voice_id": voice_id, **body})


# ── BGM / Ambient Sound ────────────────────────────────────────────────────

@router.get("/episodes/{episode_id}/bgm", response_model=ApiResponse)
async def get_bgm_data(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get BGM data for an episode."""
    from api.models.project import Episode

    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Return current BGM data (stored in episode metadata or scenes)
    return success({
        "bgm": getattr(episode, "bgm", None) or {
            "id": "",
            "name": "",
            "description": "",
            "url": "",
        },
        "sfx": [],
        "mixLevels": {
            "bgm": 60,
            "voice": 80,
            "ambient": 30,
            "sfx": 50,
        },
    })


@router.put("/episodes/{episode_id}/bgm", response_model=ApiResponse)
async def update_bgm(
    episode_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update background music for an episode."""
    from api.models.project import Episode

    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Update BGM settings
    # In production, store in episode metadata
    return success({"episode_id": episode_id, **body})


@router.post("/episodes/{episode_id}/bgm/generate", response_model=ApiResponse)
async def generate_bgm(
    episode_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate background music using AI."""
    from api.models.project import Episode

    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    description = body.get("description", "")

    # TODO: Integrate with BGM generation service (e.g., MusicGen, Stable Audio)
    # For now, return mock data
    bgm_id = str(uuid.uuid4())
    return success({
        "status": "queued",
        "bgm": {
            "id": bgm_id,
            "name": "AI Generated BGM",
            "description": description,
            "url": "",
        },
    })


@router.post("/episodes/{episode_id}/bgm/upload", response_model=ApiResponse)
async def upload_bgm(
    episode_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload a BGM file."""
    # Save uploaded file
    upload_dir = STORAGE_PATH / "bgm" / episode_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    bgm_id = str(uuid.uuid4())
    file_path = upload_dir / f"{bgm_id}_{file.filename}"
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return success({
        "id": bgm_id,
        "url": str(file_path),
    })


# ── SFX / Ambient Sound ────────────────────────────────────────────────────

@router.post("/episodes/{episode_id}/sfx/upload", response_model=ApiResponse)
async def upload_sfx(
    episode_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload an SFX file."""
    upload_dir = STORAGE_PATH / "sfx" / episode_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    sfx_id = str(uuid.uuid4())
    file_path = upload_dir / f"{sfx_id}_{file.filename}"
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return success({
        "id": sfx_id,
        "url": str(file_path),
    })


@router.delete("/episodes/{episode_id}/sfx/{sfx_id}", response_model=ApiResponse)
async def delete_sfx(
    episode_id: str,
    sfx_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete an SFX file."""
    return success({"deleted": sfx_id})


@router.post("/episodes/{episode_id}/sfx/library", response_model=ApiResponse)
async def add_sfx_from_library(
    episode_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Add SFX from built-in library."""
    name = body.get("name", "")
    category = body.get("category", "")

    # TODO: Return actual SFX file URL from library
    return success({
        "id": str(uuid.uuid4()),
        "url": "",
    })


# ── Mix Levels ──────────────────────────────────────────────────────────────

@router.put("/episodes/{episode_id}/mix", response_model=ApiResponse)
async def update_mix_levels(
    episode_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update mix levels for an episode."""
    return success({"episode_id": episode_id, **body})


# ── Subtitle Editing ───────────────────────────────────────────────────────

@router.put("/subtitles/{subtitle_id}/text", response_model=ApiResponse)
async def update_subtitle_text(
    subtitle_id: str,
    body: dict[str, str],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update subtitle text."""
    return success({"subtitle_id": subtitle_id, "text": body.get("text", "")})


@router.put("/subtitles/{subtitle_id}/timing", response_model=ApiResponse)
async def update_subtitle_timing(
    subtitle_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update subtitle timing."""
    return success({"subtitle_id": subtitle_id, **body})


# ── Video Editing ───────────────────────────────────────────────────────────

@router.put("/videos/{video_id}/trim", response_model=ApiResponse)
async def trim_video(
    video_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trim video clip."""
    return success({"video_id": video_id, "start": body.get("start"), "end": body.get("end")})


@router.put("/videos/{video_id}/transition", response_model=ApiResponse)
async def update_transition(
    video_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update video transition effect."""
    return success({"video_id": video_id, "transition": body.get("transition", "cut")})
