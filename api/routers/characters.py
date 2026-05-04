"""Character CRUD + reference sheet + wardrobe/accessories router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.character import (
    Character, CharacterCreate, CharacterOut, CharacterUpdate,
    WardrobeSpec, AppearanceSpec,
)
from api.models.project import Project
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api", tags=["characters"])


@router.post("/projects/{project_id}/characters", response_model=ApiResponse)
async def create_character(project_id: str, body: CharacterCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    character = Character(
        project_id=project_id,
        name=body.name,
        gender=body.gender,
        appearance=body.appearance.model_dump(),
        body=body.body.model_dump(),
        voice=body.voice.model_dump(),
        wardrobe_default=body.wardrobe_default.model_dump(),
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return success(CharacterOut.model_validate(character).model_dump())


@router.get("/projects/{project_id}/characters", response_model=ApiResponse)
async def list_characters(project_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(
        select(Character).where(Character.project_id == project_id).order_by(Character.created_at)
    )
    characters = result.scalars().all()
    return success([CharacterOut.model_validate(c).model_dump() for c in characters])


@router.get("/characters/{character_id}", response_model=ApiResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return success(CharacterOut.model_validate(character).model_dump())


@router.put("/characters/{character_id}", response_model=ApiResponse)
async def update_character(character_id: str, body: CharacterUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        setattr(character, key, value)
    await db.flush()
    await db.refresh(character)
    return success(CharacterOut.model_validate(character).model_dump())


@router.delete("/characters/{character_id}", response_model=ApiResponse)
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    await db.delete(character)
    return success(None)


@router.post("/characters/{character_id}/reference-sheet", response_model=ApiResponse)
async def generate_reference_sheet(character_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stub: Generate reference sheet image for character."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    # TODO: integrate with ComfyUI / image generation service
    return success({"status": "queued", "message": "Reference sheet generation queued"})


@router.get("/characters/{character_id}/wardrobe", response_model=ApiResponse)
async def get_wardrobe(character_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return success(character.wardrobe_default)


@router.post("/characters/{character_id}/wardrobe", response_model=ApiResponse)
async def update_wardrobe(character_id: str, body: WardrobeSpec, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    character.wardrobe_default = body.model_dump()
    await db.flush()
    await db.refresh(character)
    return success(character.wardrobe_default)


@router.get("/characters/{character_id}/accessories", response_model=ApiResponse)
async def get_accessories(character_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stub: Get character accessories list."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    # Accessories stored as part of wardrobe or separate field — returning empty for now
    return success([])


@router.post("/characters/{character_id}/accessories", response_model=ApiResponse)
async def add_accessory(character_id: str, body: dict[str, Any], db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stub: Add accessory to character."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    # TODO: implement accessory storage
    return success({"status": "added", "accessory": body})
