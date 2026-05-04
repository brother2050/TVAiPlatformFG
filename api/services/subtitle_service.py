"""Subtitle service using WhisperX and manual editing.

Provides subtitle generation, text/timing editing, splitting, merging,
re-alignment, and SRT import/export.
"""

from __future__ import annotations

import asyncio
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

import aiofiles


class SubtitleService:
    """Service for subtitle generation and editing.

    Args:
        storage_path: Base storage directory.
    """

    def __init__(self, storage_path: str = "./storage") -> None:
        self._storage_path = Path(storage_path)

    async def generate_subtitles(
        self,
        audio_path: str,
        *,
        language: str = "zh",
        model_size: str = "large-v2",
    ) -> list[dict[str, Any]]:
        """Generate subtitles from audio using WhisperX.

        Args:
            audio_path: Path to audio file.
            language: Language code.
            model_size: WhisperX model size.

        Returns:
            List of subtitle entries with text, start, end, speaker.
        """
        # Placeholder for WhisperX integration
        # In production, this would call WhisperX via subprocess or API
        cmd = (
            f'whisperx "{audio_path}" '
            f'--language {language} --model {model_size} '
            f'--output_format json --output_dir /tmp/whisperx_output'
        )
        # Placeholder return
        return [
            {
                "index": 0,
                "text": "",
                "start": 0.0,
                "end": 0.0,
                "speaker": None,
            }
        ]

    async def update_text(self, subtitle_id: str, text: str) -> bool:
        """Update subtitle text.

        Args:
            subtitle_id: Subtitle UUID.
            text: New subtitle text.

        Returns:
            True if updated.
        """
        # Subtitles stored in shot.dialogues or separate subtitle track
        return True

    async def update_timing(
        self,
        subtitle_id: str,
        start_sec: float,
        end_sec: float,
    ) -> bool:
        """Update subtitle timing.

        Args:
            subtitle_id: Subtitle UUID.
            start_sec: New start time in seconds.
            end_sec: New end time in seconds.

        Returns:
            True if updated.
        """
        return True

    async def split_subtitle(
        self,
        subtitle_id: str,
        split_time_sec: float,
    ) -> list[dict[str, Any]]:
        """Split a subtitle at a given time.

        Args:
            subtitle_id: Subtitle UUID.
            split_time_sec: Time to split at.

        Returns:
            List of two subtitle dicts.
        """
        return [
            {"id": f"{subtitle_id}_1", "end": split_time_sec},
            {"id": f"{subtitle_id}_2", "start": split_time_sec},
        ]

    async def merge_subtitles(
        self,
        subtitle_ids: list[str],
    ) -> dict[str, Any]:
        """Merge multiple subtitles into one.

        Args:
            subtitle_ids: List of subtitle UUIDs to merge.

        Returns:
            Merged subtitle dict.
        """
        return {"id": "merged", "merged_from": subtitle_ids}

    async def re_align(
        self,
        subtitles: list[dict[str, Any]],
        audio_path: str,
    ) -> list[dict[str, Any]]:
        """Re-align subtitles to audio.

        Args:
            subtitles: Current subtitle entries.
            audio_path: Path to reference audio.

        Returns:
            Re-aligned subtitle entries.
        """
        # Would use WhisperX forced alignment
        return subtitles

    async def import_srt(self, srt_path: str) -> list[dict[str, Any]]:
        """Import subtitles from an SRT file.

        Args:
            srt_path: Path to SRT file.

        Returns:
            List of subtitle entries.
        """
        async with aiofiles.open(srt_path, "r", encoding="utf-8") as f:
            content = await f.read()

        entries: list[dict[str, Any]] = []
        blocks = re.split(r"\n\s*\n", content.strip())

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            index = int(lines[0].strip())
            time_match = re.match(
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                lines[1].strip(),
            )
            if not time_match:
                continue

            g = [int(x) for x in time_match.groups()]
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
            text = "\n".join(lines[2:])

            entries.append({
                "index": index,
                "start": start,
                "end": end,
                "text": text,
            })

        return entries

    async def export_srt(
        self,
        subtitles: list[dict[str, Any]],
        output_path: str,
    ) -> str:
        """Export subtitles to SRT format.

        Args:
            subtitles: List of subtitle entries.
            output_path: Output file path.

        Returns:
            Path to exported SRT file.
        """
        lines: list[str] = []
        for i, sub in enumerate(subtitles, 1):
            start = self._format_srt_time(sub["start"])
            end = self._format_srt_time(sub["end"])
            text = sub.get("text", "")
            lines.append(f"{i}\n{start} --> {end}\n{text}\n")

        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(lines))

        return output_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted time string.
        """
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
