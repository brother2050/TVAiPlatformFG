"""Production pipeline router — produce, progress, batch."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.production import ProductionTask, ProductionTaskOut, ProductionProgress
from api.models.project import Episode
from api.models.script import Scene, Shot
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api", tags=["production"])

# Ordered pipeline stages
STAGES = ["keyframes", "clips", "voices", "bgm", "subtitles", "timeline", "composite"]


class BatchProduceRequest(BaseModel):
    """Request body for batch production endpoint."""
    stages: list[str] = Field(..., description="List of stages to produce")


async def _run_stage(stage: str, episode_id: str, db: AsyncSession) -> dict[str, Any]:
    """Execute a single production stage.

    Args:
        stage: Stage name (keyframes, clips, voices, etc.)
        episode_id: Episode UUID.
        db: Database session.

    Returns:
        Stage result dict.
    """
    # Update task status to processing
    stmt = (
        update(ProductionTask)
        .where(
            ProductionTask.episode_id == episode_id,
            ProductionTask.stage == stage,
        )
        .values(status="processing")
    )
    await db.execute(stmt)
    await db.commit()

    # Execute stage-specific logic
    if stage == "keyframes":
        # Generate keyframe images via ComfyUI
        # TODO: Integrate with ComfyUI service
        pass

    elif stage == "clips":
        # Assemble clips from keyframes
        # TODO: Implement clip assembly
        pass

    elif stage == "voices":
        # Generate TTS for all dialogues
        # TODO: Integrate with TTS service
        pass

    elif stage == "bgm":
        # Generate or select background music
        # TODO: Implement BGM generation
        pass

    elif stage == "subtitles":
        # Generate subtitles from dialogues
        # TODO: Implement subtitle generation
        pass

    elif stage == "timeline":
        # Assemble final timeline
        # TODO: Implement timeline assembly
        pass

    elif stage == "composite":
        # Composite video output
        # TODO: Integrate with video compositing
        pass

    # Update task status to completed
    stmt = (
        update(ProductionTask)
        .where(
            ProductionTask.episode_id == episode_id,
            ProductionTask.stage == stage,
        )
        .values(status="completed")
    )
    await db.execute(stmt)
    await db.commit()

    return {"stage": stage, "status": "completed"}


@router.post("/episodes/{episode_id}/produce", response_model=ApiResponse)
async def produce_episode(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start production pipeline for an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Check for existing tasks
    result = await db.execute(
        select(ProductionTask).where(ProductionTask.episode_id == episode_id)
    )
    existing_tasks = result.scalars().all()

    if not existing_tasks:
        # Create tasks for all stages
        tasks = []
        for stage in STAGES:
            task = ProductionTask(
                id=str(uuid.uuid4()),
                episode_id=episode_id,
                stage=stage,
                status="pending",
            )
            db.add(task)
            tasks.append(task)
        await db.flush()
        await db.commit()

    # Start production in background
    # TODO: Implement proper background task queue
    asyncio.create_task(_run_stage("keyframes", episode_id, db))

    return success({"status": "started", "episode_id": episode_id})


@router.get("/episodes/{episode_id}/progress", response_model=ApiResponse)
async def get_progress(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get production progress for an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    result = await db.execute(
        select(ProductionTask).where(ProductionTask.episode_id == episode_id)
    )
    tasks = result.scalars().all()

    status_map = {t.stage: t.status for t in tasks}
    stage_progress = []
    for stage in STAGES:
        s = status_map.get(stage, "pending")
        if s == "completed":
            progress = 100.0
        elif s == "processing":
            progress = 50.0
        elif s == "review":
            progress = 90.0
        else:
            progress = 0.0
        stage_progress.append({"stage": stage, "status": s, "progress": progress})

    overall = (
        sum(sp["progress"] for sp in stage_progress) / len(STAGES)
        if STAGES
        else 0.0
    )
    return success(
        ProductionProgress(
            episode_id=episode_id,
            stages=stage_progress,
            overall_progress=overall,
        ).model_dump()
    )


@router.post("/episodes/{episode_id}/produce/batch", response_model=ApiResponse)
async def batch_produce(
    episode_id: str,
    body: BatchProduceRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start batch production for multiple stages."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    stages = body.stages

    # Validate stages
    invalid_stages = [s for s in stages if s not in STAGES]
    if invalid_stages:
        return error(message=f"Invalid stages: {invalid_stages}")

    # Create or update tasks for specified stages
    for stage in stages:
        # Check if task exists
        result = await db.execute(
            select(ProductionTask).where(
                ProductionTask.episode_id == episode_id,
                ProductionTask.stage == stage,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Reset status to pending if not completed
            if existing.status != "completed":
                existing.status = "pending"
        else:
            task = ProductionTask(
                id=str(uuid.uuid4()),
                episode_id=episode_id,
                stage=stage,
                status="pending",
            )
            db.add(task)

    await db.commit()

    # Start batch production
    for stage in stages:
        asyncio.create_task(_run_stage(stage, episode_id, db))

    return success({"status": "batch_queued", "stages": stages, "episode_id": episode_id})


@router.post("/shots/{shot_id}/regenerate-keyframe", response_model=ApiResponse)
async def regenerate_keyframe(
    shot_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Regenerate keyframe image for a shot via ComfyUI."""
    shot = await db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    # TODO: Integrate with ComfyUI image generation service
    # This would:
    # 1. Extract visual description from shot
    # 2. Send to ComfyUI workflow
    # 3. Queue the task and return status

    return success({
        "status": "queued",
        "shot_id": shot_id,
        "message": "Keyframe regeneration queued",
    })


@router.post("/dialogues/{dialogue_id}/regenerate-voice", response_model=ApiResponse)
async def regenerate_voice(
    dialogue_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Regenerate voice/TTS for a specific dialogue."""
    # Find the dialogue
    result = await db.execute(
        select(Shot).where(Shot.dialogues.contains([{"id": dialogue_id}]))
    )
    shot = result.scalar_one_or_none()

    if not shot:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    # TODO: Integrate with TTS service
    # This would:
    # 1. Extract dialogue text and emotion
    # 2. Send to TTS service
    # 3. Queue the task and return status

    return success({
        "status": "queued",
        "dialogue_id": dialogue_id,
        "message": "Voice regeneration queued",
    })
