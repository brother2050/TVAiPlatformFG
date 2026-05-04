"""Template CRUD, version management, import/export router."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import get_db
from api.models.template import JSONTemplate, TemplateCreate, TemplateOut, TemplateUpdate
from api.routers import ApiResponse, success, error

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Path to builtin template JSON files
BUILTIN_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "json_templates"


@router.get("", response_model=ApiResponse)
async def list_templates(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(JSONTemplate).order_by(JSONTemplate.category, JSONTemplate.name))
    templates = result.scalars().all()
    return success([TemplateOut.model_validate(t).model_dump() for t in templates])


@router.get("/{slug}", response_model=ApiResponse)
async def get_template(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return success(TemplateOut.model_validate(template).model_dump())


@router.post("", response_model=ApiResponse)
async def create_template(body: TemplateCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    # Check uniqueness
    existing = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Template with slug '{body.slug}' already exists")
    template = JSONTemplate(
        name=body.name,
        slug=body.slug,
        category=body.category,
        description=body.description,
        schema=body.schema_definition,
        example=body.example,
        system_prompt_suffix=body.system_prompt_suffix,
        is_builtin=False,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return success(TemplateOut.model_validate(template).model_dump())


@router.put("/{slug}", response_model=ApiResponse)
async def update_template(slug: str, body: TemplateUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    template.version += 1
    await db.flush()
    await db.refresh(template)
    return success(TemplateOut.model_validate(template).model_dump())


@router.delete("/{slug}", response_model=ApiResponse)
async def delete_template(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete builtin template")
    await db.delete(template)
    return success(None)


@router.post("/{slug}/reset", response_model=ApiResponse)
async def reset_template(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Reset a builtin template to its original JSON file content."""
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    json_file = BUILTIN_TEMPLATES_DIR / f"{slug}.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="Builtin template file not found")
    data = json.loads(json_file.read_text(encoding="utf-8"))
    template.schema_definition = data.get("schema", {})
    template.example = data.get("example", {})
    template.system_prompt_suffix = data.get("system_prompt_suffix", "")
    template.version += 1
    await db.flush()
    return success(None)


@router.post("/{slug}/preview", response_model=ApiResponse)
async def preview_template(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Preview template with example data filled in."""
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return success({
        "schema": template.schema_definition,
        "example": template.example,
        "system_prompt_suffix": template.system_prompt_suffix,
    })


@router.post("/import", response_model=ApiResponse)
async def import_template(body: dict[str, Any], db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Import a template from JSON data."""
    slug = body.get("slug")
    if not slug:
        raise HTTPException(status_code=400, detail="slug is required")
    existing = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Template with slug '{slug}' already exists")
    template = JSONTemplate(
        name=body.get("name", slug),
        slug=slug,
        category=body.get("category", "script"),
        description=body.get("description", ""),
        schema=body.get("schema", {}),
        example=body.get("example", {}),
        system_prompt_suffix=body.get("system_prompt_suffix", ""),
        is_builtin=False,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return success(TemplateOut.model_validate(template).model_dump())


@router.get("/{slug}/export", response_model=ApiResponse)
async def export_template(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Export template as JSON."""
    result = await db.execute(select(JSONTemplate).where(JSONTemplate.slug == slug))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return success({
        "name": template.name,
        "slug": template.slug,
        "category": template.category,
        "description": template.description,
        "schema": template.schema_definition,
        "example": template.example,
        "system_prompt_suffix": template.system_prompt_suffix,
        "version": template.version,
    })
