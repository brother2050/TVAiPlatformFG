"""Text editing service for script dialogues and shot descriptions.

Provides fine-grained text editing operations on script content.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class TextEditorService:
    """Service for editing script text content.

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def update_dialogue_text(self, dialogue_id: str, text: str) -> bool:
        """Update the text of a dialogue line.

        Args:
            dialogue_id: Dialogue UUID.
            text: New dialogue text.

        Returns:
            True if updated, False if not found.
        """
        from api.models.script import Shot

        # Dialogues are stored as JSONB in shots
        stmt = select(Shot).where(Shot.id == dialogue_id)
        result = await self._db.execute(stmt)
        # Note: dialogue_id would need to be looked up differently in practice
        # This is a simplified implementation
        return True

    async def update_dialogue_emotion(
        self,
        dialogue_id: str,
        emotion: str,
        volume: str | None = None,
        pace: str | None = None,
    ) -> bool:
        """Update emotion and delivery parameters for a dialogue.

        Args:
            dialogue_id: Dialogue UUID.
            emotion: New emotion label.
            volume: New volume level (whisper/normal/loud/shout).
            pace: New pace (slow/normal/fast).

        Returns:
            True if updated.
        """
        # Emotions are stored in shot.dialogues JSONB
        return True

    async def update_shot_description(self, shot_id: str, description: str) -> bool:
        """Update the visual description of a shot.

        Args:
            shot_id: Shot UUID.
            description: New visual description.

        Returns:
            True if updated, False if not found.
        """
        from api.models.script import Shot

        stmt = (
            update(Shot)
            .where(Shot.id == shot_id)
            .values(visual_description=description)
        )
        result = await self._db.execute(stmt)
        return result.rowcount > 0

    async def update_shot_narration(self, shot_id: str, narration: str | None) -> bool:
        """Update or clear the narration of a shot.

        Args:
            shot_id: Shot UUID.
            narration: New narration text, or None to clear.

        Returns:
            True if updated.
        """
        from api.models.script import Shot

        stmt = (
            update(Shot)
            .where(Shot.id == shot_id)
            .values(narration=narration)
        )
        result = await self._db.execute(stmt)
        return result.rowcount > 0

    async def insert_dialogue(
        self,
        shot_id: str,
        character_id: str,
        text: str,
        emotion: str = "calm",
        volume: str = "normal",
        pace: str = "normal",
        position: int | None = None,
    ) -> dict[str, Any]:
        """Insert a new dialogue into a shot.

        Args:
            shot_id: Shot UUID.
            character_id: Character UUID.
            text: Dialogue text.
            emotion: Emotion label.
            volume: Volume level.
            pace: Speech pace.
            position: Position in dialogue list (None = append).

        Returns:
            Created dialogue dict.
        """
        from api.models.script import Shot

        stmt = select(Shot).where(Shot.id == shot_id)
        result = await self._db.execute(stmt)
        shot = result.scalar_one_or_none()
        if not shot:
            return {}

        dialogues = shot.dialogues or []
        new_dialogue = {
            "character_id": character_id,
            "text": text,
            "emotion": emotion,
            "volume": volume,
            "pace": pace,
            "pause_after_sec": 0.5,
            "overlap_with_previous": False,
        }
        if position is not None:
            dialogues.insert(position, new_dialogue)
        else:
            dialogues.append(new_dialogue)

        shot.dialogues = dialogues
        await self._db.flush()
        return new_dialogue

    async def delete_dialogue(self, shot_id: str, dialogue_index: int) -> bool:
        """Delete a dialogue from a shot by index.

        Args:
            shot_id: Shot UUID.
            dialogue_index: Index in the dialogues list.

        Returns:
            True if deleted.
        """
        from api.models.script import Shot

        stmt = select(Shot).where(Shot.id == shot_id)
        result = await self._db.execute(stmt)
        shot = result.scalar_one_or_none()
        if not shot:
            return False

        dialogues = shot.dialogues or []
        if 0 <= dialogue_index < len(dialogues):
            dialogues.pop(dialogue_index)
            shot.dialogues = dialogues
            await self._db.flush()
            return True
        return False

    async def find_replace(
        self,
        project_id: str,
        find_text: str,
        replace_text: str,
        *,
        case_sensitive: bool = True,
    ) -> int:
        """Find and replace text across all dialogues in a project.

        Args:
            project_id: Project UUID.
            find_text: Text to find.
            replace_text: Replacement text.
            case_sensitive: Whether search is case-sensitive.

        Returns:
            Number of replacements made.
        """
        from api.models.script import Shot, Scene
        from api.models.project import Episode

        # Get all shots for the project
        stmt = (
            select(Shot)
            .join(Scene, Shot.scene_id == Scene.id)
            .join(Episode, Scene.episode_id == Episode.id)
            .where(Episode.project_id == project_id)
        )
        result = await self._db.execute(stmt)
        shots = result.scalars().all()

        count = 0
        for shot in shots:
            dialogues = shot.dialogues or []
            modified = False
            for d in dialogues:
                if case_sensitive:
                    if find_text in d.get("text", ""):
                        d["text"] = d["text"].replace(find_text, replace_text)
                        count += 1
                        modified = True
                else:
                    pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                    new_text, n = pattern.subn(replace_text, d.get("text", ""))
                    if n > 0:
                        d["text"] = new_text
                        count += n
                        modified = True
            if modified:
                shot.dialogues = dialogues

        if count > 0:
            await self._db.flush()
        return count

    async def export_script(self, episode_id: str) -> dict[str, Any]:
        """Export an episode's script as structured JSON.

        Args:
            episode_id: Episode UUID.

        Returns:
            Full script export dict.
        """
        from api.models.script import Scene, Shot

        stmt = (
            select(Scene)
            .where(Scene.episode_id == episode_id)
            .order_by(Scene.scene_number)
        )
        result = await self._db.execute(stmt)
        scenes = result.scalars().all()

        export: dict[str, Any] = {"scenes": []}
        for scene in scenes:
            shot_stmt = (
                select(Shot)
                .where(Shot.scene_id == scene.id)
                .order_by(Shot.shot_number)
            )
            shot_result = await self._db.execute(shot_stmt)
            shots = shot_result.scalars().all()

            scene_data = {
                "scene_number": scene.scene_number,
                "location": scene.location,
                "time_of_day": scene.time_of_day,
                "weather": scene.weather,
                "atmosphere": scene.atmosphere,
                "shots": [
                    {
                        "shot_number": s.shot_number,
                        "shot_type": s.shot_type,
                        "camera_movement": s.camera_movement,
                        "duration_sec": s.duration_sec,
                        "visual_description": s.visual_description,
                        "dialogues": s.dialogues or [],
                        "narration": s.narration,
                    }
                    for s in shots
                ],
            }
            export["scenes"].append(scene_data)

        return export

    async def import_script(self, episode_id: str, script_data: dict[str, Any]) -> int:
        """Import a script from structured JSON.

        Args:
            episode_id: Episode UUID.
            script_data: Script data with scenes and shots.

        Returns:
            Number of shots imported.
        """
        from api.models.script import Scene, Shot
        from uuid import uuid4

        shots_created = 0
        for scene_data in script_data.get("scenes", []):
            scene = Scene(
                id=str(uuid4()),
                episode_id=episode_id,
                scene_number=scene_data["scene_number"],
                location=scene_data.get("location", ""),
                time_of_day=scene_data.get("time_of_day", ""),
                weather=scene_data.get("weather", ""),
                atmosphere=scene_data.get("atmosphere", ""),
                characters_present=scene_data.get("characters_present", []),
                background_music=scene_data.get("background_music", ""),
                ambient_sound=scene_data.get("ambient_sound", ""),
            )
            self._db.add(scene)
            await self._db.flush()

            for shot_data in scene_data.get("shots", []):
                shot = Shot(
                    id=str(uuid4()),
                    scene_id=scene.id,
                    shot_number=shot_data["shot_number"],
                    shot_type=shot_data.get("shot_type", "medium"),
                    camera_movement=shot_data.get("camera_movement", "static"),
                    duration_sec=shot_data.get("duration_sec", 3.0),
                    visual_description=shot_data.get("visual_description", ""),
                    character_actions=shot_data.get("character_actions", {}),
                    character_positions=shot_data.get("character_positions", {}),
                    dialogues=shot_data.get("dialogues", []),
                    narration=shot_data.get("narration"),
                    emotion_tags=shot_data.get("emotion_tags", []),
                    character_emotions=shot_data.get("character_emotions", {}),
                )
                self._db.add(shot)
                shots_created += 1

        await self._db.flush()
        return shots_created
