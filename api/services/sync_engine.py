"""Audio-video-subtitle synchronization engine.

Aligns voice, subtitles, BGM, and SFX to video timeline.
Handles fade in/out and cross-fade processing.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any


class SyncEngine:
    """Engine for synchronizing multi-track timelines.

    Handles alignment of video, voice-over, subtitles, BGM, and SFX
    into a coherent timeline for final composition.
    """

    def __init__(self, storage_path: str = "./storage") -> None:
        self._storage_path = Path(storage_path)

    async def sync_timeline(
        self,
        video_path: str,
        voice_path: str | None = None,
        subtitles: list[dict[str, Any]] | None = None,
        bgm_path: str | None = None,
        sfx_tracks: list[dict[str, Any]] | None = None,
        *,
        video_duration_sec: float = 0.0,
    ) -> dict[str, Any]:
        """Synchronize all tracks to the video timeline.

        Args:
            video_path: Path to the video file.
            voice_path: Path to voice-over audio.
            subtitles: List of subtitle entries.
            bgm_path: Path to background music.
            sfx_tracks: List of SFX tracks with timing.
            video_duration_sec: Expected video duration.

        Returns:
            Timeline dict with aligned tracks and metadata.
        """
        # Get actual video duration if not provided
        if video_duration_sec <= 0:
            video_duration_sec = await self._get_duration(video_path)

        timeline: dict[str, Any] = {
            "video": {
                "path": video_path,
                "duration_sec": video_duration_sec,
            },
            "voice": None,
            "subtitles": [],
            "bgm": None,
            "sfx": [],
            "total_duration_sec": video_duration_sec,
        }

        # Align voice to video
        if voice_path:
            voice_info = await self.align_voice_to_video(voice_path, video_duration_sec)
            timeline["voice"] = voice_info

        # Align subtitles to voice
        if subtitles and voice_path:
            aligned_subs = await self.align_subtitle_to_voice(subtitles, voice_path)
            timeline["subtitles"] = aligned_subs
        elif subtitles:
            timeline["subtitles"] = subtitles

        # Add BGM with fade
        if bgm_path:
            timeline["bgm"] = {
                "path": bgm_path,
                "start_sec": 0,
                "duration_sec": video_duration_sec,
                "fade_in_sec": 1.0,
                "fade_out_sec": 2.0,
                "volume": 0.3,
            }

        # Add SFX tracks
        if sfx_tracks:
            for sfx in sfx_tracks:
                timeline["sfx"].append({
                    "path": sfx.get("path", ""),
                    "start_sec": sfx.get("start_sec", 0),
                    "volume": sfx.get("volume", 0.8),
                    "fade_in_sec": sfx.get("fade_in_sec", 0.1),
                    "fade_out_sec": sfx.get("fade_out_sec", 0.2),
                })

        return timeline

    async def align_voice_to_video(
        self,
        voice_path: str,
        target_duration_sec: float,
    ) -> dict[str, Any]:
        """Align voice-over to video duration.

        If voice is shorter, pad with silence.
        If voice is longer, adjust speed slightly.

        Args:
            voice_path: Path to voice audio.
            target_duration_sec: Target video duration.

        Returns:
            Dict with aligned voice info.
        """
        voice_duration = await self._get_duration(voice_path)
        speed_factor = 1.0

        if voice_duration > target_duration_sec * 1.05:
            # Voice too long — speed up slightly
            speed_factor = voice_duration / target_duration_sec
            speed_factor = min(speed_factor, 1.2)  # Cap at 20% speedup
        elif voice_duration < target_duration_sec * 0.9:
            # Voice too short — will be padded
            pass

        return {
            "path": voice_path,
            "original_duration_sec": voice_duration,
            "aligned_duration_sec": target_duration_sec,
            "speed_factor": speed_factor,
            "needs_padding": voice_duration < target_duration_sec,
            "fade_in_sec": 0.3,
            "fade_out_sec": 0.5,
        }

    async def align_subtitle_to_voice(
        self,
        subtitles: list[dict[str, Any]],
        voice_path: str,
        *,
        min_gap_sec: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Align subtitles to voice-over timing.

        Ensures subtitles don't overlap and have minimum gaps.

        Args:
            subtitles: List of subtitle entries with start/end times.
            voice_path: Path to voice audio for reference.
            min_gap_sec: Minimum gap between consecutive subtitles.

        Returns:
            Aligned subtitle entries.
        """
        if not subtitles:
            return []

        # Sort by start time
        sorted_subs = sorted(subtitles, key=lambda s: s.get("start", 0))
        aligned: list[dict[str, Any]] = []

        for i, sub in enumerate(sorted_subs):
            entry = dict(sub)

            # Ensure minimum gap from previous
            if aligned:
                prev_end = aligned[-1].get("end", 0)
                if entry.get("start", 0) < prev_end + min_gap_sec:
                    entry["start"] = prev_end + min_gap_sec

            # Ensure start < end
            if entry.get("end", 0) <= entry.get("start", 0):
                entry["end"] = entry["start"] + 1.0

            aligned.append(entry)

        return aligned

    async def apply_fade(
        self,
        audio_path: str,
        fade_in_sec: float = 0.5,
        fade_out_sec: float = 0.5,
    ) -> str:
        """Apply fade in/out to an audio track.

        Args:
            audio_path: Path to source audio.
            fade_in_sec: Fade in duration.
            fade_out_sec: Fade out duration.

        Returns:
            Path to faded audio.
        """
        output_path = str(Path(audio_path).with_stem(Path(audio_path).stem + "_faded"))
        duration = await self._get_duration(audio_path)
        fade_out_start = max(0, duration - fade_out_sec)

        cmd = (
            f'ffmpeg -y -i "{audio_path}" '
            f'-af "afade=t=in:st=0:d={fade_in_sec},afade=t=out:st={fade_out_start}:d={fade_out_sec}" '
            f'-c:a flac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def _get_duration(self, file_path: str) -> float:
        """Get duration of an audio/video file.

        Args:
            file_path: Path to media file.

        Returns:
            Duration in seconds.
        """
        cmd = (
            f'ffprobe -v error -show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except (ValueError, TypeError):
            return 0.0
