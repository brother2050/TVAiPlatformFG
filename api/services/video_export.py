"""Video export service - FFmpeg-based video compositing and export."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from api.config import settings


class VideoExportService:
    """Service for video compositing and export using FFmpeg."""

    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.export_path = self.storage_path / "exports"
        self.export_path.mkdir(parents=True, exist_ok=True)

    async def composite_video(
        self,
        episode_id: str,
        timeline: dict[str, Any],
        export_settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Composite video from timeline data.

        Args:
            episode_id: Episode identifier.
            timeline: Timeline data containing tracks.
            export_settings: Export settings (resolution, codec, fps, quality).

        Returns:
            Export result with status and output path.
        """
        export_id = str(uuid.uuid4())
        output_path = self.export_path / f"{export_id}.mp4"

        # Build FFmpeg command
        cmd = self._build_composite_cmd(timeline, export_settings, output_path)

        # Execute FFmpeg
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "export_id": export_id,
                    "status": "completed",
                    "output_path": str(output_path),
                    "output_url": f"/api/media/exports/{export_id}.mp4",
                    "file_size": output_path.stat().st_size if output_path.exists() else 0,
                }
            else:
                return {
                    "export_id": export_id,
                    "status": "failed",
                    "error": stderr.decode() if stderr else "Unknown error",
                }
        except FileNotFoundError:
            return {
                "export_id": export_id,
                "status": "failed",
                "error": "FFmpeg not found. Please install FFmpeg.",
            }
        except Exception as e:
            return {
                "export_id": export_id,
                "status": "failed",
                "error": str(e),
            }

    def _build_composite_cmd(
        self,
        timeline: dict[str, Any],
        settings: dict[str, Any],
        output_path: Path,
    ) -> list[str]:
        """Build FFmpeg command for video compositing."""
        resolution = settings.get("resolution", "1920x1080")
        fps = settings.get("fps", 30)
        codec = settings.get("codec", "libx264")
        quality = settings.get("quality", 23)

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={resolution}:d={timeline.get('duration', 10)}:r={fps}",
        ]

        # Add watermark if provided
        if settings.get("watermark"):
            cmd.extend(["-i", settings["watermark"]])

        # Add main video source placeholder
        cmd.extend(["-i", str(self.storage_path / "temp" / "composed.mp4")])

        # Add subtitle overlay
        subtitle_file = self.storage_path / "temp" / f"{uuid.uuid4()}.srt"
        if timeline.get("subtitles"):
            self._generate_subtitle_file(timeline["subtitles"], subtitle_file)
            cmd.extend(["-vf", f"subtitles={subtitle_file}"])

        # Video encoding settings
        if codec == "libx264":
            cmd.extend(["-c:v", "libx264", "-crf", str(quality), "-preset", "medium", "-pix_fmt", "yuv420p"])
        elif codec == "libx265":
            cmd.extend(["-c:v", "libx265", "-crf", str(quality), "-preset", "medium", "-pix_fmt", "yuv420p"])
        elif codec == "libvpx-vp9":
            cmd.extend(["-c:v", "libvpx-vp9", "-crf", str(quality), "-b:v", "0"])

        # Audio settings
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        cmd.append(str(output_path))
        return cmd

    def _generate_subtitle_file(self, subtitles: list[dict], output_path: Path) -> None:
        """Generate SRT subtitle file from subtitle data."""
        lines = []
        for i, sub in enumerate(subtitles, 1):
            start = self._format_srt_time(sub.get("start", 0))
            end = self._format_srt_time(sub.get("end", 0))
            text = sub.get("text", "").replace("\n", " ")
            lines.extend([str(i), f"{start} --> {end}", text, ""])
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def batch_export(
        self,
        episodes: list[str],
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Batch export multiple episodes."""
        results = await asyncio.gather(
            *[self._export_single(ep, settings) for ep in episodes],
            return_exceptions=True,
        )
        return {
            "total": len(episodes),
            "completed": sum(1 for r in results if not isinstance(r, Exception)),
            "failed": sum(1 for r in results if isinstance(r, Exception)),
        }

    async def _export_single(self, episode_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        """Export single episode."""
        return {"episode_id": episode_id, "status": "queued"}

    def get_export_status(self, export_id: str) -> dict[str, Any]:
        """Get export status by ID."""
        export_file = self.export_path / f"{export_id}.mp4"
        if not export_file.exists():
            return {"export_id": export_id, "status": "not_found"}
        return {
            "export_id": export_id,
            "status": "completed",
            "output_path": str(export_file),
            "file_size": export_file.stat().st_size,
        }

    def list_exports(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent exports."""
        exports = []
        for f in sorted(self.export_path.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            exports.append({
                "export_id": f.stem,
                "filename": f.name,
                "file_size": f.stat().st_size,
                "created_at": f.stat().st_ctime,
            })
        return exports


_export_service: VideoExportService | None = None


def get_export_service() -> VideoExportService:
    """Get or create video export service instance."""
    global _export_service
    if _export_service is None:
        _export_service = VideoExportService(settings.storage.local_path)
    return _export_service
