"""Episode management API router."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models import Episode, Project

router = APIRouter(prefix="/api/episodes", tags=["episodes"])


class EpisodeResponse(BaseModel):
    id: str
    project_id: str
    episode_number: int
    title: str
    synopsis: str
    status: str
    duration_sec: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CreateEpisodeDto(BaseModel):
    project_id: str
    episode_number: int
    title: str = ""
    synopsis: str = ""


class UpdateEpisodeDto(BaseModel):
    title: Optional[str] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None
    duration_sec: Optional[int] = None


@router.get("", response_model=dict)
async def list_episodes(
    project_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """List all episodes for a project."""
    result = await db.execute(
        select(Episode)
        .where(Episode.project_id == project_id)
        .order_by(Episode.episode_number)
    )
    episodes = result.scalars().all()
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": e.id,
                "project_id": e.project_id,
                "episode_number": e.episode_number,
                "title": e.title or f"第{e.episode_number}集",
                "synopsis": e.synopsis or "",
                "status": e.status or "draft",
                "duration_sec": e.duration_sec,
                "created_at": e.created_at.isoformat() if e.created_at else "",
                "updated_at": e.updated_at.isoformat() if e.updated_at else "",
            }
            for e in episodes
        ],
    }


@router.get("/{episode_id}", response_model=dict)
async def get_episode(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get episode details."""
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": episode.id,
            "project_id": episode.project_id,
            "episode_number": episode.episode_number,
            "title": episode.title or f"第{episode.episode_number}集",
            "synopsis": episode.synopsis or "",
            "status": episode.status or "draft",
            "duration_sec": episode.duration_sec,
            "created_at": episode.created_at.isoformat() if episode.created_at else "",
            "updated_at": episode.updated_at.isoformat() if episode.updated_at else "",
        },
    }


@router.post("", response_model=dict)
async def create_episode(
    data: CreateEpisodeDto,
    db: AsyncSession = Depends(get_db),
):
    """Create a new episode."""
    # Check project exists
    result = await db.execute(select(Project).where(Project.id == data.project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    episode = Episode(
        project_id=data.project_id,
        episode_number=data.episode_number,
        title=data.title or f"第{data.episode_number}集",
        synopsis=data.synopsis,
        status="draft",
    )
    db.add(episode)
    await db.commit()
    await db.refresh(episode)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": episode.id,
            "project_id": episode.project_id,
            "episode_number": episode.episode_number,
            "title": episode.title,
            "synopsis": episode.synopsis,
            "status": episode.status,
            "duration_sec": episode.duration_sec,
            "created_at": episode.created_at.isoformat() if episode.created_at else "",
            "updated_at": episode.updated_at.isoformat() if episode.updated_at else "",
        },
    }


@router.put("/{episode_id}", response_model=dict)
async def update_episode(
    episode_id: str,
    data: UpdateEpisodeDto,
    db: AsyncSession = Depends(get_db),
):
    """Update episode details."""
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    if data.title is not None:
        episode.title = data.title
    if data.synopsis is not None:
        episode.synopsis = data.synopsis
    if data.status is not None:
        episode.status = data.status
    if data.duration_sec is not None:
        episode.duration_sec = data.duration_sec

    await db.commit()
    await db.refresh(episode)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": episode.id,
            "project_id": episode.project_id,
            "episode_number": episode.episode_number,
            "title": episode.title,
            "synopsis": episode.synopsis,
            "status": episode.status,
            "duration_sec": episode.duration_sec,
            "created_at": episode.created_at.isoformat() if episode.created_at else "",
            "updated_at": episode.updated_at.isoformat() if episode.updated_at else "",
        },
    }


@router.delete("/{episode_id}", response_model=dict)
async def delete_episode(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete episode."""
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    await db.delete(episode)
    await db.commit()

    return {"code": 0, "message": "success", "data": None}


# Episode script endpoints
class ScriptContent(BaseModel):
    scenes: list = Field(default_factory=list)


@router.get("/{episode_id}/script", response_model=dict)
async def get_episode_script(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get episode script content."""
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "episode_id": episode_id,
            "scenes": [],
        },
    }


@router.put("/{episode_id}/script", response_model=dict)
async def update_episode_script(
    episode_id: str,
    data: ScriptContent,
    db: AsyncSession = Depends(get_db),
):
    """Update episode script content."""
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "episode_id": episode_id,
            "scenes": data.scenes,
        },
    }
