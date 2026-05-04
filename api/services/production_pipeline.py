"""Production pipeline orchestration.

Manages the 7-stage production workflow for each episode:
1. Keyframes — AI generates keyframe images
2. Clips — Image-to-video generation
3. Voices — TTS synthesis
4. BGM — Background music generation
5. Subtitles — WhisperX subtitle generation
6. Timeline — Audio/video/subtitle alignment
7. Composite — Final video composition

Each stage: AI generation → mark for review → wait for human approval.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.comfyui_runner import ComfyUIClientAdapter
from api.services.ffmpeg_service import FFmpegService
from api.services.subtitle_service import SubtitleService
from api.services.sync_engine import SyncEngine
from api.services.tts_service import TTSService


# Production stages in order
STAGES = ["keyframes", "clips", "voices", "bgm", "subtitles", "timeline", "composite"]


class ProductionPipeline:
    """Orchestrates the multi-stage production pipeline.

    Args:
        db: Async SQLAlchemy session.
        comfyui: ComfyUI client for image/video generation.
        tts: TTS service for voice synthesis.
        subtitle: Subtitle service for subtitle generation.
        sync: Sync engine for timeline alignment.
        ffmpeg: FFmpeg service for final composition.
    """

    def __init__(
        self,
        db: AsyncSession,
        comfyui: ComfyUIClientAdapter,
        tts: TTSService,
        subtitle: SubtitleService,
        sync: SyncEngine,
        ffmpeg: FFmpegService,
    ) -> None:
        self._db = db
        self._comfyui = comfyui
        self._tts = tts
        self._subtitle = subtitle
        self._sync = sync
        self._ffmpeg = ffmpeg

    async def produce_episode(
        self,
        episode_id: str,
        *,
        start_stage: str | None = None,
    ) -> dict[str, Any]:
        """Run the full production pipeline for an episode.

        Each stage generates assets, then marks them for human review.
        The pipeline pauses at each review checkpoint.

        Args:
            episode_id: Episode UUID.
            start_stage: Stage to start from (default: first stage).

        Returns:
            Dict with pipeline status and task info.
        """
        # Create production tasks for each stage
        tasks: list[dict[str, Any]] = []
        start_idx = STAGES.index(start_stage) if start_stage else 0

        for stage in STAGES[start_idx:]:
            task = await self._create_task(episode_id, stage)
            tasks.append(task)

        return {
            "episode_id": episode_id,
            "tasks": tasks,
            "status": "started",
            "current_stage": STAGES[start_idx],
        }

    async def produce_batch(
        self,
        episode_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Start production for multiple episodes.

        Args:
            episode_ids: List of episode UUIDs.

        Returns:
            List of pipeline status dicts.
        """
        results: list[dict[str, Any]] = []
        for ep_id in episode_ids:
            result = await self.produce_episode(ep_id)
            results.append(result)
        return results

    async def wait_for_review(
        self,
        task_id: str,
        *,
        approved: bool = True,
        notes: str = "",
    ) -> dict[str, Any]:
        """Handle review completion for a production task.

        Args:
            task_id: Production task UUID.
            approved: Whether the task was approved.
            notes: Review notes.

        Returns:
            Updated task status.
        """
        from api.models.production import ProductionTask

        stmt = select(ProductionTask).where(ProductionTask.id == task_id)
        result = await self._db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        if approved:
            task.status = "completed"
            task.review_notes = notes
            await self._db.flush()

            # Trigger next stage
            next_stage = self._get_next_stage(task.stage)
            if next_stage:
                next_task = await self._create_task(task.episode_id, next_stage)
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "next_stage": next_stage,
                    "next_task": next_task,
                }
            return {"task_id": task_id, "status": "completed", "message": "All stages complete!"}
        else:
            task.status = "failed"
            task.review_notes = notes
            await self._db.flush()
            return {"task_id": task_id, "status": "rejected", "notes": notes}

    async def run_stage(
        self,
        episode_id: str,
        stage: str,
    ) -> dict[str, Any]:
        """Execute a specific production stage.

        Args:
            episode_id: Episode UUID.
            stage: Stage name.

        Returns:
            Stage execution result.
        """
        stage_handlers = {
            "keyframes": self._run_keyframes,
            "clips": self._run_clips,
            "voices": self._run_voices,
            "bgm": self._run_bgm,
            "subtitles": self._run_subtitles,
            "timeline": self._run_timeline,
            "composite": self._run_composite,
        }

        handler = stage_handlers.get(stage)
        if not handler:
            return {"error": f"Unknown stage: {stage}"}

        return await handler(episode_id)

    # ------------------------------------------------------------------
    # Stage implementations
    # ------------------------------------------------------------------

    async def _run_keyframes(self, episode_id: str) -> dict[str, Any]:
        """Generate keyframe images for all shots in an episode.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with generated keyframe paths.
        """
        from api.models.script import Scene, Shot

        stmt = (
            select(Shot)
            .join(Scene, Shot.scene_id == Scene.id)
            .where(Scene.episode_id == episode_id)
            .order_by(Scene.scene_number, Shot.shot_number)
        )
        result = await self._db.execute(stmt)
        shots = result.scalars().all()

        keyframes: dict[str, str] = {}
        for shot in shots:
            kf_result = await self._comfyui.generate_keyframe(
                visual_description=shot.visual_description or "",
            )
            if kf_result.get("image_path"):
                keyframes[shot.id] = kf_result["image_path"]

        return {"keyframes": keyframes, "count": len(keyframes)}

    async def _run_clips(self, episode_id: str) -> dict[str, Any]:
        """Generate video clips from keyframes.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with generated clip paths.
        """
        # Placeholder — would iterate over shots and generate videos
        return {"clips": {}, "count": 0}

    async def _run_voices(self, episode_id: str) -> dict[str, Any]:
        """Generate voice-over audio for all dialogues.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with generated audio paths.
        """
        # Placeholder — would iterate over dialogues and synthesize
        return {"voices": {}, "count": 0}

    async def _run_bgm(self, episode_id: str) -> dict[str, Any]:
        """Generate or assign background music.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with BGM paths.
        """
        return {"bgm": {}, "count": 0}

    async def _run_subtitles(self, episode_id: str) -> dict[str, Any]:
        """Generate subtitles from voice audio.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with subtitle data.
        """
        return {"subtitles": [], "count": 0}

    async def _run_timeline(self, episode_id: str) -> dict[str, Any]:
        """Align all tracks into a synchronized timeline.

        Args:
            episode_id: Episode UUID.

        Returns:
            Timeline alignment result.
        """
        return {"timeline": {}, "aligned": True}

    async def _run_composite(self, episode_id: str) -> dict[str, Any]:
        """Compose the final video.

        Args:
            episode_id: Episode UUID.

        Returns:
            Dict with final video path.
        """
        return {"output_path": "", "duration_sec": 0}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _create_task(self, episode_id: str, stage: str) -> dict[str, Any]:
        """Create a production task for a stage.

        Args:
            episode_id: Episode UUID.
            stage: Stage name.

        Returns:
            Created task dict.
        """
        from api.models.production import ProductionTask

        task = ProductionTask(
            id=str(uuid4()),
            episode_id=episode_id,
            stage=stage,
            status="pending",
            assets={},
            review_notes="",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(task)
        await self._db.flush()

        return {
            "id": task.id,
            "episode_id": episode_id,
            "stage": stage,
            "status": "pending",
        }

    def _get_next_stage(self, current_stage: str) -> str | None:
        """Get the next production stage.

        Args:
            current_stage: Current stage name.

        Returns:
            Next stage name, or None if current is last.
        """
        try:
            idx = STAGES.index(current_stage)
            if idx + 1 < len(STAGES):
                return STAGES[idx + 1]
        except ValueError:
            pass
        return None
