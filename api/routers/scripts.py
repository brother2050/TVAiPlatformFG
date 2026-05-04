"""Script generation, storyboard, and shot editing router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.base import get_db
from api.models.script import Scene, Shot, ShotUpdate, ShotOut, SceneOut
from api.models.project import Episode
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api", tags=["scripts"])


@router.post("/episodes/{episode_id}/generate-script", response_model=ApiResponse)
async def generate_script(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stub: AI-powered script generation for an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    # TODO: integrate with Dify / LLM service
    return success({"status": "queued", "message": "Script generation queued"})


@router.get("/episodes/{episode_id}/script", response_model=ApiResponse)
async def get_script(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get all scenes (with shots) for an episode — the 'script' view."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    result = await db.execute(
        select(Scene)
        .where(Scene.episode_id == episode_id)
        .options(selectinload(Scene.shots))
        .order_by(Scene.scene_number)
    )
    scenes = result.scalars().all()
    return success([SceneOut.model_validate(s).model_dump() for s in scenes])


@router.put("/episodes/{episode_id}/script", response_model=ApiResponse)
async def update_script(episode_id: str, body: list[dict[str, Any]], db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Bulk update the script (scenes + shots) for an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    # TODO: implement full scene/shot upsert logic
    return success({"status": "updated", "scene_count": len(body)})


@router.post("/episodes/{episode_id}/split-storyboard", response_model=ApiResponse)
async def split_storyboard(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stub: Split script into storyboard shots."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    # TODO: integrate with Dify / LLM service
    return success({"status": "queued", "message": "Storyboard splitting queued"})


@router.get("/episodes/{episode_id}/storyboard", response_model=ApiResponse)
async def get_storyboard(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get storyboard (scenes + shots) for an episode."""
    result = await db.execute(
        select(Scene)
        .where(Scene.episode_id == episode_id)
        .options(selectinload(Scene.shots))
        .order_by(Scene.scene_number)
    )
    scenes = result.scalars().all()
    storyboard = []
    for scene in scenes:
        scene_data = SceneOut.model_validate(scene).model_dump()
        storyboard.append(scene_data)
    return success(storyboard)


@router.put("/shots/{shot_id}", response_model=ApiResponse)
async def update_shot(shot_id: str, body: ShotUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    shot = await db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(shot, key, value)
    await db.flush()
    await db.refresh(shot)
    return success(ShotOut.model_validate(shot).model_dump())
