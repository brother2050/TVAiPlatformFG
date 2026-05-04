"""Script generation service.

Orchestrates script creation, storyboard splitting, and dialogue generation
by delegating to DifyClient with appropriate templates.
"""

from __future__ import annotations

from typing import Any

from api.services.dify_client import DifyClient


class ScriptService:
    """Service for AI-powered script generation.

    Args:
        dify: DifyClient instance for LLM calls.
    """

    def __init__(self, dify: DifyClient) -> None:
        self._dify = dify

    async def generate_script(
        self,
        project_id: str,
        template_example: dict[str, Any],
        project_settings_context: str,
        user_prompt: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a full script using Dify.

        Args:
            project_id: Project UUID.
            template_example: Script template example JSON.
            project_settings_context: Serialized project settings.
            user_prompt: User's creative direction / prompt.
            conversation_id: Optional for multi-turn generation.

        Returns:
            Generated script as structured JSON.
        """
        return await self._dify.generate_script(
            template_example=template_example,
            project_settings_context=project_settings_context,
            user_input=user_prompt,
            conversation_id=conversation_id,
        )

    async def split_storyboard(
        self,
        template_example: dict[str, Any],
        project_settings_context: str,
        script_content: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Split a script into storyboard shots.

        Args:
            template_example: Storyboard template example JSON.
            project_settings_context: Serialized project settings.
            script_content: The script text to break down.
            conversation_id: Optional for multi-turn.

        Returns:
            Storyboard with scenes and shots as structured JSON.
        """
        return await self._dify.generate_storyboard(
            template_example=template_example,
            project_settings_context=project_settings_context,
            script_content=script_content,
            conversation_id=conversation_id,
        )

    async def generate_dialogues(
        self,
        template_example: dict[str, Any],
        project_settings_context: str,
        scene_description: str,
        characters_context: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate dialogues for a scene.

        Args:
            template_example: Dialogue template example JSON.
            project_settings_context: Serialized project settings.
            scene_description: Description of the scene.
            characters_context: Character profiles for voice consistency.
            conversation_id: Optional for multi-turn.

        Returns:
            Generated dialogues as structured JSON.
        """
        return await self._dify.generate_dialogues(
            template_example=template_example,
            project_settings_context=project_settings_context,
            scene_description=scene_description,
            characters_context=characters_context,
            conversation_id=conversation_id,
        )
