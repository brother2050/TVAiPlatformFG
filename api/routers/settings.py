"""Project global settings and scene overrides router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.project import Project, ProjectGlobalSettings
from api.models.script import Scene
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api", tags=["settings"])


def _ensure_project(project: Any) -> None:
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/projects/{project_id}/settings", response_model=ApiResponse)
async def get_settings(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    _ensure_project(project)
    return success(project.global_settings)


@router.put("/projects/{project_id}/settings", response_model=ApiResponse)
async def update_settings(project_id: str, body: ProjectGlobalSettings, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    _ensure_project(project)
    project.global_settings = body.model_dump()
    await db.flush()
    await db.refresh(project)
    return success(project.global_settings)


@router.post("/projects/{project_id}/settings/dimensions", response_model=ApiResponse)
async def add_dimension(project_id: str, body: dict[str, str], db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    _ensure_project(project)
    key = body.get("key")
    value = body.get("value")
    if not key:
        raise HTTPException(status_code=400, detail="key is required")
    custom_dims = project.global_settings.get("custom_dimensions", {})
    custom_dims[key] = value or ""
    project.global_settings["custom_dimensions"] = custom_dims
    await db.flush()
    return success(None)


@router.delete("/projects/{project_id}/settings/dimensions/{key}", response_model=ApiResponse)
async def remove_dimension(project_id: str, key: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    _ensure_project(project)
    custom_dims = project.global_settings.get("custom_dimensions", {})
    custom_dims.pop(key, None)
    project.global_settings["custom_dimensions"] = custom_dims
    await db.flush()
    return success(None)


@router.get("/projects/{project_id}/scenes/{scene_id}/overrides", response_model=ApiResponse)
async def get_scene_overrides(project_id: str, scene_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    scene = await db.get(Scene, scene_id)
    if not scene or scene.episode_id is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return success(scene.scene_overrides or {})


@router.put("/projects/{project_id}/scenes/{scene_id}/overrides", response_model=ApiResponse)
async def update_scene_overrides(
    project_id: str, scene_id: str, body: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    scene = await db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    scene.scene_overrides = body
    await db.flush()
    await db.refresh(scene)
    return success(scene.scene_overrides)
