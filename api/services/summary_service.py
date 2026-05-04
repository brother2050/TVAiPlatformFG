"""Summary service for managing project/arc/episode summaries.

Provides CRUD operations and regeneration for hierarchical summaries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.context_compressor import ContextCompressor


class SummaryService:
    """Service for managing summaries at project, arc, and episode levels.

    Args:
        db: Async SQLAlchemy session.
        compressor: ContextCompressor for LLM-based summary generation.
    """

    def __init__(self, db: AsyncSession, compressor: ContextCompressor) -> None:
        self._db = db
        self._compressor = compressor

    async def get_project_summary(self, project_id: str) -> dict[str, Any] | None:
        """Get the project-level summary.

        Args:
            project_id: Project UUID.

        Returns:
            Summary dict or None.
        """
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "project",
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def get_arc_summaries(self, project_id: str) -> list[dict[str, Any]]:
        """Get all arc-level summaries for a project.

        Args:
            project_id: Project UUID.

        Returns:
            List of arc summary dicts.
        """
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "arc",
        ).order_by(Summary.arc_name)
        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def get_episode_summaries(self, project_id: str) -> list[dict[str, Any]]:
        """Get all episode-level summaries for a project.

        Args:
            project_id: Project UUID.

        Returns:
            List of episode summary dicts ordered by episode number.
        """
        from api.models.summary import Summary

        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == "episode",
        ).order_by(Summary.episode_number)
        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def save_summary(
        self,
        project_id: str,
        summary_type: str,
        content: str,
        *,
        episode_number: int | None = None,
        arc_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save a summary (create or update).

        Args:
            project_id: Project UUID.
            summary_type: One of project/arc/episode.
            content: Summary text content.
            episode_number: Episode number (for episode type).
            arc_name: Arc name (for arc type).
            metadata: Additional metadata (key_events, character_changes, etc.).

        Returns:
            Saved summary dict.
        """
        from api.models.summary import Summary

        # Try to find existing
        stmt = select(Summary).where(
            Summary.project_id == project_id,
            Summary.summary_type == summary_type,
        )
        if episode_number is not None:
            stmt = stmt.where(Summary.episode_number == episode_number)
        if arc_name is not None:
            stmt = stmt.where(Summary.arc_name == arc_name)

        result = await self._db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.extra_data = metadata or {}
            existing.generated_at = datetime.now(timezone.utc)
            return self._to_dict(existing)

        summary = Summary(
            id=str(uuid4()),
            project_id=project_id,
            summary_type=summary_type,
            episode_number=episode_number,
            arc_name=arc_name,
            content=content,
            extra_data=metadata or {},
            generated_at=datetime.now(timezone.utc),
        )
        self._db.add(summary)
        await self._db.flush()
        return self._to_dict(summary)

    async def regenerate_summary(
        self,
        project_id: str,
        summary_type: str,
        *,
        episode_number: int | None = None,
        arc_name: str | None = None,
        scenes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Regenerate a summary using LLM.

        Args:
            project_id: Project UUID.
            summary_type: One of project/arc/episode.
            episode_number: Episode number (for episode type).
            arc_name: Arc name (for arc type).
            scenes: Scene data (for episode regeneration).

        Returns:
            Regenerated summary dict.
        """
        if summary_type == "episode" and episode_number is not None:
            content = await self._compressor.generate_episode_summary(
                project_id, episode_number, scenes or []
            )
        elif summary_type == "arc" and arc_name is not None:
            ep_summaries = await self._get_episode_contents(project_id)
            content = await self._compressor.generate_arc_summary(
                project_id, arc_name, ep_summaries
            )
        elif summary_type == "project":
            arc_summaries = await self._get_arc_contents(project_id)
            content = await self._compressor.update_project_summary(
                project_id, arc_summaries
            )
        else:
            raise ValueError(f"Invalid summary_type={summary_type} or missing required params")

        return await self.save_summary(
            project_id=project_id,
            summary_type=summary_type,
            content=content,
            episode_number=episode_number,
            arc_name=arc_name,
        )

    async def _get_episode_contents(self, project_id: str) -> list[str]:
        """Get all episode summary contents."""
        from api.models.summary import Summary

        stmt = select(Summary.content).where(
            Summary.project_id == project_id,
            Summary.summary_type == "episode",
        ).order_by(Summary.episode_number)
        result = await self._db.execute(stmt)
        return [row[0] for row in result.all()]

    async def _get_arc_contents(self, project_id: str) -> list[str]:
        """Get all arc summary contents."""
        from api.models.summary import Summary

        stmt = select(Summary.content).where(
            Summary.project_id == project_id,
            Summary.summary_type == "arc",
        )
        result = await self._db.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    def _to_dict(summary: Any) -> dict[str, Any]:
        """Convert summary ORM to dict."""
        return {
            "id": summary.id,
            "project_id": summary.project_id,
            "summary_type": summary.summary_type,
            "episode_number": summary.episode_number,
            "arc_name": summary.arc_name,
            "content": summary.content,
            "metadata": summary.extra_data,
            "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
        }
