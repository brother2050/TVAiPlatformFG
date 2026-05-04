"""Context compression engine for long-running series.

Builds hierarchical summaries (project → arc → episode) with sliding window
to keep LLM context within token limits.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.dify_client import DifyClient


class ContextCompressor:
    """Compress and manage context for multi-episode projects.

    Uses layered summaries: project-level, arc-level, and episode-level,
    with a sliding window for recent content.

    Args:
        db: Async SQLAlchemy session.
        dify: DifyClient for LLM-based summarization.
        max_context_tokens: Approximate max tokens for context window.
    """

    def __init__(
        self,
        db: AsyncSession,
        dify: DifyClient,
        max_context_tokens: int = 8000,
    ) -> None:
        self._db = db
        self._dify = dify
        self._max_context_tokens = max_context_tokens

    async def build_context_for_episode(
        self,
        project_id: str,
        episode_number: int,
        *,
        window_size: int = 3,
    ) -> str:
        """Build a compressed context for generating a specific episode.

        Layers:
        1. Project summary (condensed overview)
        2. Arc summary (if episode is part of an arc)
        3. Recent episode summaries (sliding window)
        4. Current episode's detailed scenes (if any exist)

        Args:
            project_id: Project UUID.
            episode_number: Target episode number.
            window_size: Number of recent episodes to include in detail.

        Returns:
            Formatted context string for LLM.
        """
        sections: list[str] = []

        # 1. Project summary
        project_summary = await self._get_project_summary(project_id)
        if project_summary:
            sections.append(f"## Project Overview\n{project_summary}")

        # 2. Arc summary
        arc_name = self._detect_arc(episode_number)
        if arc_name:
            arc_summary = await self._get_arc_summary(project_id, arc_name)
            if arc_summary:
                sections.append(f"## Current Arc: {arc_name}\n{arc_summary}")

        # 3. Recent episode summaries (sliding window)
        start_ep = max(1, episode_number - window_size)
        for ep_num in range(start_ep, episode_number):
            ep_summary = await self._get_episode_summary(project_id, ep_num)
            if ep_summary:
                sections.append(f"## Episode {ep_num} Summary\n{ep_summary}")

        return "\n\n".join(sections) if sections else "No prior context available."

    async def generate_episode_summary(
        self,
        project_id: str,
        episode_number: int,
        scenes: list[dict[str, Any]],
    ) -> str:
        """Generate a summary for an episode from its scenes.

        Args:
            project_id: Project UUID.
            episode_number: Episode number.
            scenes: List of scene dicts with shots and dialogues.

        Returns:
            Generated summary text.
        """
        scene_text = self._format_scenes_for_summary(scenes)
        prompt = (
            f"Summarize Episode {episode_number} in 200-300 words. "
            "Focus on: key events, character developments, plot twists, emotional beats.\n\n"
            f"Scenes:\n{scene_text}"
        )
        result = await self._dify.generate_script(
            template_example={"summary": "string", "key_events": [], "character_changes": {}},
            project_settings_context="",
            user_input=prompt,
        )
        return result.get("summary", result.get("raw_answer", ""))

    async def generate_arc_summary(
        self,
        project_id: str,
        arc_name: str,
        episode_summaries: list[str],
    ) -> str:
        """Generate an arc-level summary from episode summaries.

        Args:
            project_id: Project UUID.
            arc_name: Name of the story arc.
            episode_summaries: Summaries of episodes in this arc.

        Returns:
            Arc summary text.
        """
        combined = "\n\n".join(
            f"Episode {i + 1}: {s}" for i, s in enumerate(episode_summaries)
        )
        prompt = (
            f"Summarize the '{arc_name}' story arc in 150-200 words. "
            "Focus on the overarching narrative, character arcs, and themes.\n\n"
            f"Episode summaries:\n{combined}"
        )
        result = await self._dify.generate_script(
            template_example={"arc_summary": "string"},
            project_settings_context="",
            user_input=prompt,
        )
        return result.get("arc_summary", result.get("raw_answer", ""))

    async def update_project_summary(
        self,
        project_id: str,
        arc_summaries: list[str],
    ) -> str:
        """Generate/update the project-level summary from arc summaries.

        Args:
            project_id: Project UUID.
            arc_summaries: Summaries of all arcs.

        Returns:
            Project summary text.
        """
        combined = "\n\n".join(arc_summaries)
        prompt = (
            "Summarize this entire project in 100-150 words. "
            "Capture the essence: genre, main characters, central conflict, tone.\n\n"
            f"Arc summaries:\n{combined}"
        )
        result = await self._dify.generate_script(
            template_example={"project_summary": "string"},
            project_settings_context="",
            user_input=prompt,
        )
        return result.get("project_summary", result.get("raw_answer", ""))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_project_summary(self, project_id: str) -> str:
        """Fetch project-level summary from DB."""
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "project",
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return row.content if row else ""

    async def _get_arc_summary(self, project_id: str, arc_name: str) -> str:
        """Fetch arc-level summary from DB."""
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "arc",
            Summary.arc_name == arc_name,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return row.content if row else ""

    async def _get_episode_summary(self, project_id: str, episode_number: int) -> str:
        """Fetch episode-level summary from DB."""
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "episode",
            Summary.episode_number == episode_number,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return row.content if row else ""

    def _detect_arc(self, episode_number: int) -> str:
        """Detect which arc an episode belongs to.

        Simple heuristic: every 3-4 episodes form an arc.

        Args:
            episode_number: Episode number.

        Returns:
            Arc name string.
        """
        arc_num = (episode_number - 1) // 4 + 1
        return f"Arc {arc_num}"

    def _format_scenes_for_summary(self, scenes: list[dict[str, Any]]) -> str:
        """Format scenes into text for summarization.

        Args:
            scenes: List of scene dicts.

        Returns:
            Formatted text.
        """
        parts: list[str] = []
        for scene in scenes:
            loc = scene.get("location", "Unknown")
            time = scene.get("time_of_day", "")
            desc = scene.get("description", "")
            shots = scene.get("shots", [])
            parts.append(f"Scene @ {loc} ({time}): {desc}")
            for shot in shots[:3]:  # Limit to first 3 shots for brevity
                parts.append(f"  - Shot: {shot.get('visual_description', '')[:100]}")
        return "\n".join(parts)
