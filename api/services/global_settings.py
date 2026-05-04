"""Global settings service for project-wide configuration.

Manages art style, color palette, narrative pace, custom dimensions,
scene overrides, and prompt context generation.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class GlobalSettingsService:
    """Service for managing project global settings.

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_settings(self, project_id: str) -> dict[str, Any]:
        """Get global settings for a project.

        Args:
            project_id: Project UUID.

        Returns:
            Global settings dict.
        """
        from api.models.project import Project

        stmt = select(Project).where(Project.id == project_id)
        result = await self._db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            return {}
        return project.global_settings or {}

    async def update_settings(self, project_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        """Update global settings for a project.

        Args:
            project_id: Project UUID.
            settings: New settings to merge.

        Returns:
            Updated settings dict.
        """
        from api.models.project import Project

        stmt = select(Project).where(Project.id == project_id)
        result = await self._db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            return {}

        current = project.global_settings or {}
        current.update(settings)
        project.global_settings = current
        await self._db.flush()
        return current

    async def add_dimension(self, project_id: str, key: str, value: str) -> None:
        """Add a custom dimension to project settings.

        Args:
            project_id: Project UUID.
            key: Dimension key name.
            value: Dimension value.
        """
        settings = await self.get_settings(project_id)
        custom = settings.get("custom_dimensions", {})
        custom[key] = value
        settings["custom_dimensions"] = custom
        await self.update_settings(project_id, settings)

    async def remove_dimension(self, project_id: str, key: str) -> bool:
        """Remove a custom dimension from project settings.

        Args:
            project_id: Project UUID.
            key: Dimension key to remove.

        Returns:
            True if removed, False if key not found.
        """
        settings = await self.get_settings(project_id)
        custom = settings.get("custom_dimensions", {})
        if key not in custom:
            return False
        del custom[key]
        settings["custom_dimensions"] = custom
        await self.update_settings(project_id, settings)
        return True

    async def get_scene_overrides(self, project_id: str) -> dict[str, Any]:
        """Get scene-level overrides for a project.

        Args:
            project_id: Project UUID.

        Returns:
            Dict mapping scene_id → override settings.
        """
        settings = await self.get_settings(project_id)
        return settings.get("scene_overrides", {})

    async def update_scene_overrides(
        self, project_id: str, scene_id: str, overrides: dict[str, Any]
    ) -> dict[str, Any]:
        """Update overrides for a specific scene.

        Args:
            project_id: Project UUID.
            scene_id: Scene UUID.
            overrides: Override settings to apply.

        Returns:
            Updated scene overrides.
        """
        settings = await self.get_settings(project_id)
        scene_overrides = settings.get("scene_overrides", {})
        scene_overrides[scene_id] = overrides
        settings["scene_overrides"] = scene_overrides
        await self.update_settings(project_id, settings)
        return overrides

    async def to_prompt_context(self, project_id: str) -> str:
        """Convert project settings to a formatted prompt context string.

        This context is injected into LLM prompts to guide generation.

        Args:
            project_id: Project UUID.

        Returns:
            Formatted settings context string.
        """
        settings = await self.get_settings(project_id)
        if not settings:
            return "No project settings configured."

        lines: list[str] = ["## Project Global Settings"]
        field_map = {
            "art_style": "Art Style",
            "color_palette": "Color Palette",
            "narrative_pace": "Narrative Pace",
            "target_audience": "Target Audience",
            "overall_mood": "Overall Mood",
            "music_style": "Music Style",
            "subtitle_style": "Subtitle Style",
            "global_prompt_prefix": "Global Prompt Prefix",
        }
        for key, label in field_map.items():
            value = settings.get(key)
            if value:
                lines.append(f"- {label}: {value}")

        custom = settings.get("custom_dimensions", {})
        if custom:
            lines.append("\n## Custom Dimensions")
            for key, value in custom.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)
