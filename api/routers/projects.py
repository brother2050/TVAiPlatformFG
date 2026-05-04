"""Project & Episode CRUD router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.project import (
    Episode, EpisodeCreate, EpisodeOut, EpisodeUpdate,
    Project, ProjectCreate, ProjectGlobalSettings, ProjectOut, ProjectUpdate,
)
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api", tags=["projects"])


# ── Projects ────────────────────────────────────────────────────────────────

@router.post("/projects", response_model=ApiResponse)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = Project(
        title=body.title,
        genre=body.genre,
        style=body.style,
        total_episodes=body.total_episodes,
        episode_duration_sec=body.episode_duration_sec,
        global_settings=body.global_settings.model_dump(),
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return success(ProjectOut.model_validate(project).model_dump())


@router.get("/projects", response_model=ApiResponse)
async def list_projects(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return success([ProjectOut.model_validate(p).model_dump() for p in projects])


@router.get("/projects/{project_id}", response_model=ApiResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return success(ProjectOut.model_validate(project).model_dump())


@router.put("/projects/{project_id}", response_model=ApiResponse)
async def update_project(project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    await db.flush()
    await db.refresh(project)
    return success(ProjectOut.model_validate(project).model_dump())


@router.delete("/projects/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    return success(None)


@router.post("/projects/{project_id}/duplicate", response_model=ApiResponse)
async def duplicate_project(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    new_project = Project(
        title=f"{project.title} (副本)",
        genre=project.genre,
        style=project.style,
        total_episodes=project.total_episodes,
        episode_duration_sec=project.episode_duration_sec,
        global_settings=project.global_settings,
        status="draft",
    )
    db.add(new_project)
    await db.flush()
    await db.refresh(new_project)
    return success(ProjectOut.model_validate(new_project).model_dump())


# ── Episodes ────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/episodes", response_model=ApiResponse)
async def create_episode(project_id: str, body: EpisodeCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    episode = Episode(
        project_id=project_id,
        episode_number=body.episode_number,
        title=body.title,
        synopsis=body.synopsis,
    )
    db.add(episode)
    await db.flush()
    await db.refresh(episode)
    return success(EpisodeOut.model_validate(episode).model_dump())


@router.get("/projects/{project_id}/episodes", response_model=ApiResponse)
async def list_episodes(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(
        select(Episode).where(Episode.project_id == project_id).order_by(Episode.episode_number)
    )
    episodes = result.scalars().all()
    return success([EpisodeOut.model_validate(e).model_dump() for e in episodes])


@router.get("/episodes/{episode_id}", response_model=ApiResponse)
async def get_episode(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return success(EpisodeOut.model_validate(episode).model_dump())


@router.put("/episodes/{episode_id}", response_model=ApiResponse)
async def update_episode(episode_id: str, body: EpisodeUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(episode, key, value)
    await db.flush()
    await db.refresh(episode)
    return success(EpisodeOut.model_validate(episode).model_dump())


@router.delete("/episodes/{episode_id}", response_model=ApiResponse)
async def delete_episode(episode_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    await db.delete(episode)
    return success(None)
