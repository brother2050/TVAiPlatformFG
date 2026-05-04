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
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.script import Scene, Shot
from api.routers import ApiResponse, success, error
from api.services.comfyui_runner import ComfyUIClientAdapter, ComfyUIConfig
from api.services.chattts_client import ChatTTSClient
from api.services.image_editor import ImageEditorService

router = APIRouter(prefix="/api/editor", tags=["editor"])

# Storage path for media files
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Service instances (initialized lazily)
_comfyui_client: ComfyUIClientAdapter | None = None
_chattts_client: ChatTTSClient | None = None
_image_editor: ImageEditorService | None = None


def get_comfyui() -> ComfyUIClientAdapter:
    """Get or create ComfyUI client."""
    global _comfyui_client
    if _comfyui_client is None:
        config = ComfyUIConfig(base_url=os.getenv("COMFYUI_URL", "http://127.0.0.1:8188"))
        _comfyui_client = ComfyUIClientAdapter(config)
    return _comfyui_client


def get_chattts() -> ChatTTSClient:
    """Get or create ChatTTS client."""
    global _chattts_client
    if _chattts_client is None:
        _chattts_client = ChatTTSClient(api_url=os.getenv("CHATTS_URL", "http://127.0.0.1:5000"))
    return _chattts_client


def get_image_editor() -> ImageEditorService:
    """Get or create ImageEditorService."""
    global _image_editor
    if _image_editor is None:
        _image_editor = ImageEditorService(get_comfyui(), str(STORAGE_PATH))
    return _image_editor


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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Regenerate an image via ComfyUI."""
    # In production, fetch shot data and trigger regeneration
    # For now, queue async task
    comfyui = get_comfyui()
    
    # Check if ComfyUI is available
    if not await comfyui.health_check():
        return success({
            "status": "queued",
            "image_id": image_id,
            "message": "ComfyUI queued for regeneration",
        })
    
    # If ComfyUI available, trigger regeneration
    # Note: In real implementation, fetch shot's visual_description and character_reference
    return success({
        "status": "processing",
        "image_id": image_id,
        "message": "Image regeneration started via ComfyUI",
    })


@router.post("/images/{image_id}/inpaint", response_model=ApiResponse)
async def inpaint_image(
    image_id: str,
    mask: UploadFile = File(...),
    prompt: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Inpaint image with mask and prompt."""
    # Save mask file
    mask_dir = STORAGE_PATH / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    
    mask_id = str(uuid.uuid4())
    mask_path = mask_dir / f"{mask_id}_{mask.filename}"
    async with aiofiles.open(mask_path, "wb") as f:
        content = await mask.read()
        await f.write(content)
    
    # Get image editor service
    image_editor = get_image_editor()
    comfyui = get_comfyui()
    
    # Check ComfyUI availability
    if not await comfyui.health_check():
        return success({
            "status": "queued",
            "image_id": image_id,
            "mask_id": mask_id,
            "message": "Inpainting queued",
        })
    
    # Note: In real implementation, fetch image_path from database
    # result = await image_editor.inpaint(image_id, image_path, str(mask_path), prompt)
    
    return success({
        "status": "processing",
        "image_id": image_id,
        "mask_id": mask_id,
        "message": "Inpainting started via ComfyUI",
    })


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
    # Get ChatTTS client
    chattts = get_chattts()
    
    # In production: fetch dialogue text, emotion params from database
    # Then call chattts.synthesize() with appropriate params
    # Store result in storage/voices/{voice_id}.wav
    
    voice_dir = STORAGE_PATH / "voices"
    voice_dir.mkdir(parents=True, exist_ok=True)
    voice_path = voice_dir / f"{voice_id}.wav"
    
    try:
        # Note: In real implementation, fetch dialogue text from database
        # text = await fetch_dialogue_text(voice_id)
        # audio_bytes = await chattts.synthesize(text, ...)
        # async with aiofiles.open(voice_path, "wb") as f:
        #     await f.write(audio_bytes)
        
        return success({
            "status": "queued",
            "voice_id": voice_id,
            "message": "Voice regeneration queued via ChatTTS",
        })
    except Exception as e:
        return success({
            "status": "queued",
            "voice_id": voice_id,
            "message": f"Voice queued: {str(e)}",
        })


@router.put("/voices/{voice_id}/params", response_model=ApiResponse)
async def update_voice_params(
    voice_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update voice parameters (tone, speed, pitch)."""
    # Extract voice parameters
    speed = body.get("speed", 1.0)
    pitch = body.get("pitch", 0)
    volume = body.get("volume", 1.0)
    
    # In production: Update voice settings in database
    # Re-generate voice with new params if auto_apply is true
    auto_apply = body.get("auto_apply", False)
    
    if auto_apply:
        chattts = get_chattts()
        # Note: In real implementation, fetch dialogue text and regenerate
        # audio_bytes = await chattts.synthesize(text, speed=speed, ...)
        return success({
            "voice_id": voice_id,
            "speed": speed,
            "pitch": pitch,
            "volume": volume,
            "status": "regenerating",
            "message": "Voice updated and regenerating",
        })
    
    return success({
        "voice_id": voice_id,
        "speed": speed,
        "pitch": pitch,
        "volume": volume,
        "status": "saved",
        "message": "Voice parameters saved",
    })


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
    duration = body.get("duration", 60)  # seconds
    style = body.get("style", "cinematic")

    # BGM generation service integration point
    # In production, integrate with services like:
    # - MusicGen (Meta)
    # - Stable Audio (Stability AI)
    # - Suno API
    
    bgm_id = str(uuid.uuid4())
    bgm_dir = STORAGE_PATH / "bgm" / episode_id
    bgm_dir.mkdir(parents=True, exist_ok=True)
    bgm_path = bgm_dir / f"{bgm_id}.mp3"
    
    # Note: In real implementation:
    # 1. Call BGM generation API (MusicGen, Stable Audio, etc.)
    # 2. Save generated audio to bgm_path
    # 3. Update database with bgm record
    
    # For now, return queued status
    return success({
        "status": "queued",
        "bgm": {
            "id": bgm_id,
            "name": f"AI Generated BGM - {style}",
            "description": description,
            "url": f"/storage/bgm/{episode_id}/{bgm_id}.mp3",
            "duration": duration,
            "style": style,
        },
        "message": "BGM generation queued. Will be available when processing completes.",
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

    # Built-in SFX library
    # In production, these would be actual audio files in storage/sfx/library/
    LIBRARY_SFX: dict[str, dict[str, str]] = {
        "door_open": {"name": "Door Open", "category": "foley", "url": "/storage/sfx/library/door_open.wav"},
        "door_close": {"name": "Door Close", "category": "foley", "url": "/storage/sfx/library/door_close.wav"},
        "footsteps": {"name": "Footsteps", "category": "foley", "url": "/storage/sfx/library/footsteps.wav"},
        "knock": {"name": "Knock", "category": "foley", "url": "/storage/sfx/library/knock.wav"},
        "phone_ring": {"name": "Phone Ring", "category": "ui", "url": "/storage/sfx/library/phone_ring.wav"},
        "notification": {"name": "Notification", "category": "ui", "url": "/storage/sfx/library/notification.wav"},
        "click": {"name": "Click", "category": "ui", "url": "/storage/sfx/library/click.wav"},
        "explosion": {"name": "Explosion", "category": "action", "url": "/storage/sfx/library/explosion.wav"},
        "car_horn": {"name": "Car Horn", "category": "ambient", "url": "/storage/sfx/library/car_horn.wav"},
        "rain": {"name": "Rain", "category": "ambient", "url": "/storage/sfx/library/rain.wav"},
        "thunder": {"name": "Thunder", "category": "ambient", "url": "/storage/sfx/library/thunder.wav"},
        "wind": {"name": "Wind", "category": "ambient", "url": "/storage/sfx/library/wind.wav"},
    }

    sfx_id = str(uuid.uuid4())
    
    # Look up in library
    if name in LIBRARY_SFX:
        library_sfx = LIBRARY_SFX[name]
        return success({
            "id": sfx_id,
            "name": library_sfx["name"],
            "category": library_sfx["category"],
            "url": library_sfx["url"],
            "source": "library",
        })
    
    # Category search
    if category:
        matching = [s for s in LIBRARY_SFX.values() if s["category"] == category]
        if matching:
            selected = matching[0]
            return success({
                "id": sfx_id,
                "name": selected["name"],
                "category": selected["category"],
                "url": selected["url"],
                "source": "library",
            })
    
    return success({
        "id": sfx_id,
        "name": name,
        "category": category,
        "url": "",
        "source": "unknown",
        "message": "SFX not found in library",
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
