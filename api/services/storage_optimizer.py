"""Storage optimization services for images, audio, and video.

Provides WebP compression, FLAC audio, H.265 video encoding,
deduplication, and automatic temp file cleanup.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiofiles


class ImageStorageOptimizer:
    """Optimize image storage with WebP compression and deduplication.

    Args:
        storage_path: Base storage directory.
        quality: WebP quality (1-100).
        max_width: Max image width before resize.
    """

    def __init__(
        self,
        storage_path: str = "./storage",
        quality: int = 85,
        max_width: int = 1920,
    ) -> None:
        self._storage_path = Path(storage_path)
        self._quality = quality
        self._max_width = max_width
        self._hash_index: dict[str, str] = {}  # hash → path

    async def compress_to_webp(self, input_path: str) -> str:
        """Compress an image to WebP format.

        Args:
            input_path: Path to the source image.

        Returns:
            Path to the compressed WebP file.
        """
        from PIL import Image

        output_path = str(Path(input_path).with_suffix(".webp"))
        img = Image.open(input_path)
        if img.width > self._max_width:
            ratio = self._max_width / img.width
            new_size = (self._max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(output_path, "WEBP", quality=self._quality)
        return output_path

    async def deduplicate(self, file_path: str) -> str:
        """Check for duplicate images by content hash.

        Args:
            file_path: Path to the image file.

        Returns:
            Path to the file (original if unique, existing if duplicate).
        """
        file_hash = await self._compute_hash(file_path)
        if file_hash in self._hash_index:
            existing = self._hash_index[file_hash]
            if Path(existing).exists():
                os.remove(file_path)
                return existing
        self._hash_index[file_hash] = file_path
        return file_path

    async def _compute_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hex digest string.
        """
        sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()


class AudioStorageOptimizer:
    """Optimize audio storage with FLAC compression.

    Args:
        storage_path: Base storage directory.
        sample_rate: Target sample rate in Hz.
    """

    def __init__(self, storage_path: str = "./storage", sample_rate: int = 22050) -> None:
        self._storage_path = Path(storage_path)
        self._sample_rate = sample_rate

    async def compress_to_flac(self, input_path: str) -> str:
        """Compress audio to FLAC format.

        Args:
            input_path: Path to the source audio file.

        Returns:
            Path to the compressed FLAC file.
        """
        output_path = str(Path(input_path).with_suffix(".flac"))
        # Use ffmpeg for conversion
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-ar {self._sample_rate} -c:a flac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def normalize_audio(self, input_path: str, target_lufs: float = -16.0) -> str:
        """Normalize audio loudness.

        Args:
            input_path: Path to source audio.
            target_lufs: Target loudness in LUFS.

        Returns:
            Path to normalized audio.
        """
        output_path = str(Path(input_path).with_suffix(".normalized.flac"))
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-af "loudnorm=I={target_lufs}:TP=-1.5:LRA=11" '
            f'-ar {self._sample_rate} -c:a flac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path


class VideoStorageOptimizer:
    """Optimize video storage with H.265 encoding.

    Args:
        storage_path: Base storage directory.
        crf: Constant Rate Factor (lower = better quality).
    """

    def __init__(self, storage_path: str = "./storage", crf: int = 23) -> None:
        self._storage_path = Path(storage_path)
        self._crf = crf

    async def compress_to_h265(self, input_path: str) -> str:
        """Compress video to H.265 (HEVC) format.

        Args:
            input_path: Path to the source video.

        Returns:
            Path to the compressed video.
        """
        output_path = str(Path(input_path).with_suffix(".h265.mp4"))
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-c:v libx265 -crf {self._crf} -preset medium '
            f'-c:a aac -b:a 128k "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path


class StorageCleaner:
    """Automatic cleanup of temporary files.

    Args:
        storage_path: Base storage directory.
        max_age_hours: Max age in hours before cleanup.
    """

    def __init__(self, storage_path: str = "./storage", max_age_hours: int = 72) -> None:
        self._storage_path = Path(storage_path)
        self._max_age = timedelta(hours=max_age_hours)

    async def clean_temp_files(self) -> dict[str, Any]:
        """Remove temporary files older than max_age.

        Returns:
            Dict with cleanup stats (files_removed, bytes_freed).
        """
        temp_dir = self._storage_path / "temp"
        if not temp_dir.exists():
            return {"files_removed": 0, "bytes_freed": 0}

        now = datetime.now(timezone.utc)
        files_removed = 0
        bytes_freed = 0

        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if now - mtime > self._max_age:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    files_removed += 1
                    bytes_freed += size

        return {"files_removed": files_removed, "bytes_freed": bytes_freed}

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage usage statistics.

        Returns:
            Dict with total_size, file_count, by_type breakdown.
        """
        total_size = 0
        file_count = 0
        by_type: dict[str, int] = {}

        if not self._storage_path.exists():
            return {"total_size": 0, "file_count": 0, "by_type": {}}

        for file_path in self._storage_path.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                file_count += 1
                ext = file_path.suffix.lower()
                by_type[ext] = by_type.get(ext, 0) + size

        return {
            "total_size": total_size,
            "file_count": file_count,
            "by_type": by_type,
        }

