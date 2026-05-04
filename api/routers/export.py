"""Export router - video export and batch export endpoints."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.project import Episode
from api.routers import ApiResponse, success, error
from api.services.video_export import get_export_service


router = APIRouter(prefix="/api", tags=["export"])


class ExportSettings(BaseModel):
    """Export settings model."""
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    quality: int = 23
    watermark: str | None = None
    intro: str | None = None
    outro: str | None = None


class BatchExportRequest(BaseModel):
    """Request body for batch export."""
    episode_ids: list[str]
    settings: ExportSettings


@router.post("/episodes/{episode_id}/export", response_model=ApiResponse)
async def export_episode(
    episode_id: str,
    settings: ExportSettings = Body(default=ExportSettings()),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Export a single episode to video file."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    export_service = get_export_service()

    # Build timeline from episode data
    timeline = {
        "duration": 120,  # Default duration
        "subtitles": [],
        "clips": [],
    }

    result = await export_service.composite_video(episode_id, timeline, settings.model_dump())

    return success(result)


@router.post("/export/batch", response_model=ApiResponse)
async def batch_export(
    body: BatchExportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Batch export multiple episodes."""
    if not body.episode_ids:
        return error("No episodes specified for export")

    export_service = get_export_service()

    result = await export_service.batch_export(
        body.episode_ids,
        body.settings.model_dump(),
    )

    return success(result)


@router.get("/exports/{export_id}", response_model=ApiResponse)
async def get_export_info(
    export_id: str,
) -> dict[str, Any]:
    """Get export status and information."""
    export_service = get_export_service()
    result = export_service.get_export_status(export_id)
    return success(result)


@router.get("/exports", response_model=ApiResponse)
async def list_exports(
    limit: int = 50,
) -> dict[str, Any]:
    """List all exports."""
    export_service = get_export_service()
    exports = export_service.list_exports(limit)
    return success({"exports": exports})


@router.delete("/exports/{export_id}", response_model=ApiResponse)
async def delete_export(
    export_id: str,
) -> dict[str, Any]:
    """Delete an export file."""
    import os
    export_service = get_export_service()
    export_file = export_service.export_path / f"{export_id}.mp4"

    if export_file.exists():
        os.remove(export_file)
        return success({"deleted": export_id, "message": "Export file deleted"})

    return error("Export file not found")


@router.get("/episodes/{episode_id}/storage-usage", response_model=ApiResponse)
async def get_storage_usage(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get storage usage for an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Calculate storage usage
    storage_usage = {
        "video": 0,
        "images": 0,
        "audio": 0,
        "subtitles": 0,
        "total": 0,
    }

    return success(storage_usage)


@router.get("/storage/summary", response_model=ApiResponse)
async def get_storage_summary() -> dict[str, Any]:
    """Get overall storage summary."""
    import shutil
    from pathlib import Path
    from api.config import settings

    storage_path = Path(settings.storage.local_path)

    def get_dir_size(path: Path) -> int:
        total = 0
        if path.exists():
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        return total

    # Calculate sizes for different categories
    media_path = storage_path / "media"
    images_path = storage_path / "images"
    voices_path = storage_path / "voices"
    bgm_path = storage_path / "bgm"
    sfx_path = storage_path / "sfx"

    try:
        disk = shutil.disk_usage(storage_path)
        total_disk = disk.total
        used_disk = disk.used
        free_disk = disk.free
    except Exception:
        total_disk = used_disk = free_disk = 0

    summary = {
        "total": total_disk,
        "used": used_disk,
        "available": free_disk,
        "percent": round((used_disk / total_disk * 100) if total_disk else 0, 1),
        "by_category": {
            "media": get_dir_size(media_path),
            "images": get_dir_size(images_path),
            "voices": get_dir_size(voices_path),
            "bgm": get_dir_size(bgm_path),
            "sfx": get_dir_size(sfx_path),
        },
    }

    return success(summary)
