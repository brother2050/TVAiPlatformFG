"""Template management service.

CRUD, version management, import/export, preview, and built-in template initialization.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class TemplateService:
    """Service for managing JSON templates (script/character/storyboard/dialogue).

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_templates(
        self,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all templates, optionally filtered by category.

        Args:
            category: Filter by template category (script/character/storyboard/dialogue).

        Returns:
            List of template dicts.
        """
        from api.models.template import JSONTemplate

        stmt = select(JSONTemplate)
        if category:
            stmt = stmt.where(JSONTemplate.category == category)
        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def get_template(self, slug: str) -> dict[str, Any] | None:
        """Get a template by slug.

        Args:
            slug: Template slug identifier.

        Returns:
            Template dict or None if not found.
        """
        from api.models.template import JSONTemplate

        stmt = select(JSONTemplate).where(JSONTemplate.slug == slug)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def create_template(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new template.

        Args:
            data: Template data (name, slug, category, schema, example, etc.).

        Returns:
            Created template dict.
        """
        from api.models.template import JSONTemplate

        template = JSONTemplate(
            id=str(uuid4()),
            name=data["name"],
            slug=data["slug"],
            category=data["category"],
            description=data.get("description", ""),
            schema_definition=data.get("schema", {}),
            example=data.get("example", {}),
            system_prompt_suffix=data.get("system_prompt_suffix", ""),
            version=1,
            is_builtin=data.get("is_builtin", False),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(template)
        await self._db.flush()
        return self._to_dict(template)

    async def update_template(self, slug: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing template and increment version.

        Args:
            slug: Template slug.
            data: Fields to update.

        Returns:
            Updated template dict or None.
        """
        from api.models.template import JSONTemplate

        stmt = select(JSONTemplate).where(JSONTemplate.slug == slug)
        result = await self._db.execute(stmt)
        template = result.scalar_one_or_none()
        if not template:
            return None

        for key, value in data.items():
            if hasattr(template, key) and key not in ("id", "created_at"):
                setattr(template, key, value)

        template.version = (template.version or 1) + 1
        template.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return self._to_dict(template)

    async def delete_template(self, slug: str) -> bool:
        """Delete a template by slug.

        Args:
            slug: Template slug.

        Returns:
            True if deleted, False if not found.
        """
        from api.models.template import JSONTemplate

        stmt = delete(JSONTemplate).where(JSONTemplate.slug == slug)
        result = await self._db.execute(stmt)
        return result.rowcount > 0

    async def get_version_history(self, slug: str) -> list[dict[str, Any]]:
        """Get version history for a template.

        Note: Current implementation returns current version info.
        Full version history would require a separate versions table.

        Args:
            slug: Template slug.

        Returns:
            List of version info dicts.
        """
        template = await self.get_template(slug)
        if not template:
            return []
        return [{"version": template["version"], "updated_at": template["updated_at"]}]

    async def revert_to_version(self, slug: str, version: int) -> dict[str, Any] | None:
        """Revert a template to a specific version.

        Note: Stub implementation — would need version history table.

        Args:
            slug: Template slug.
            version: Target version number.

        Returns:
            Reverted template dict or None.
        """
        # TODO: Implement with version history table
        return await self.get_template(slug)

    async def import_template(self, data: dict[str, Any]) -> dict[str, Any]:
        """Import a template from exported JSON.

        Args:
            data: Exported template data.

        Returns:
            Imported template dict.
        """
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        return await self.create_template(data)

    async def export_template(self, slug: str) -> dict[str, Any] | None:
        """Export a template as JSON.

        Args:
            slug: Template slug.

        Returns:
            Exportable template dict.
        """
        return await self.get_template(slug)

    async def preview(self, slug: str) -> dict[str, Any]:
        """Preview a template's expected output structure.

        Simulates what the LLM output would look like based on the template's example.

        Args:
            slug: Template slug.

        Returns:
            Preview dict with example output structure.
        """
        template = await self.get_template(slug)
        if not template:
            return {"error": "Template not found"}
        return {
            "template_name": template["name"],
            "category": template["category"],
            "example_output": template["example"],
            "schema": template["schema"],
            "system_prompt_suffix": template["system_prompt_suffix"],
        }

    async def initialize_builtin_templates(self) -> int:
        """Initialize built-in templates if they don't exist.

        Returns:
            Number of templates created.
        """
        builtin_templates = self._get_builtin_definitions()
        created = 0
        for tmpl in builtin_templates:
            existing = await self.get_template(tmpl["slug"])
            if not existing:
                await self.create_template(tmpl)
                created += 1
        return created

    def _get_builtin_definitions(self) -> list[dict[str, Any]]:
        """Return built-in template definitions.

        Returns:
            List of template data dicts.
        """
        return [
            {
                "name": "Script Writer",
                "slug": "script-writer",
                "category": "script",
                "description": "Generate episode scripts with scenes and narration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "scenes": {"type": "array", "items": {"type": "object"}},
                    },
                },
                "example": {
                    "title": "Episode 1: The Beginning",
                    "scenes": [
                        {
                            "scene_number": 1,
                            "location": "City street",
                            "time_of_day": "morning",
                            "description": "Our hero walks through the busy streets...",
                        }
                    ],
                },
                "system_prompt_suffix": "Write engaging short drama scripts.",
                "is_builtin": True,
            },
            {
                "name": "Dialogue Generator",
                "slug": "dialogue-generator",
                "category": "dialogue",
                "description": "Generate character dialogues for scenes",
                "schema": {
                    "type": "object",
                    "properties": {
                        "dialogues": {"type": "array"},
                    },
                },
                "example": {
                    "dialogues": [
                        {
                            "character": "Hero",
                            "text": "I never thought it would come to this.",
                            "emotion": "sad",
                            "volume": "normal",
                        }
                    ],
                },
                "system_prompt_suffix": "Write natural, character-consistent dialogues.",
                "is_builtin": True,
            },
            {
                "name": "Storyboard Splitter",
                "slug": "storyboard-splitter",
                "category": "storyboard",
                "description": "Split scripts into detailed shot breakdowns",
                "schema": {
                    "type": "object",
                    "properties": {
                        "shots": {"type": "array"},
                    },
                },
                "example": {
                    "shots": [
                        {
                            "shot_number": 1,
                            "shot_type": "wide",
                            "camera_movement": "static",
                            "duration_sec": 3.0,
                            "visual_description": "Wide establishing shot of the city at dawn",
                        }
                    ],
                },
                "system_prompt_suffix": "Create detailed storyboard breakdowns.",
                "is_builtin": True,
            },
            {
                "name": "Character Designer",
                "slug": "character-designer",
                "category": "character",
                "description": "Generate character appearance and personality profiles",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "appearance": {"type": "object"},
                        "personality": {"type": "string"},
                    },
                },
                "example": {
                    "name": "Alex",
                    "appearance": {
                        "face_shape": "oval",
                        "eye_color": "hazel",
                        "hair_style": "messy medium",
                        "hair_color": "dark brown",
                    },
                    "personality": "Determined, slightly sarcastic, loyal to friends",
                },
                "system_prompt_suffix": "Design compelling characters for short dramas.",
                "is_builtin": True,
            },
        ]

    @staticmethod
    def _to_dict(template: Any) -> dict[str, Any]:
        """Convert a template ORM object to dict.

        Args:
            template: JSONTemplate ORM instance.

        Returns:
            Serializable dict.
        """
        return {
            "id": template.id,
            "name": template.name,
            "slug": template.slug,
            "category": template.category,
            "description": template.description,
            "schema": template.schema_definition,
            "example": template.example,
            "system_prompt_suffix": template.system_prompt_suffix,
            "version": template.version,
            "is_builtin": template.is_builtin,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
