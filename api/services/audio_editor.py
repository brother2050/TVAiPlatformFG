"""Audio editing service for voice/TTS operations.

Provides regeneration, upload/replace, parameter adjustment,
silence trimming, denoising, and batch operations.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiofiles

from api.services.tts_service import TTSService


class AudioEditorService:
    """Service for editing voice/audio assets.

    Args:
        tts: TTSService for voice regeneration.
        storage_path: Base storage directory.
    """

    def __init__(self, tts: TTSService, storage_path: str = "./storage") -> None:
        self._tts = tts
        self._storage_path = Path(storage_path)

    async def regenerate(
        self,
        dialogue_id: str,
        text: str,
        character_voice: dict[str, Any] | None = None,
        emotion: str = "calm",
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """Regenerate voice audio for a dialogue.

        Args:
            dialogue_id: Dialogue UUID.
            text: Text to synthesize.
            character_voice: Character voice spec.
            emotion: Emotion label.
            params: Additional TTS parameters.

        Returns:
            Audio bytes (FLAC format).
        """
        return await self._tts.synthesize(
            text=text,
            character_voice=character_voice,
            emotion=emotion,
            params=params,
        )

    async def upload_replace(self, dialogue_id: str, file_path: str) -> str:
        """Replace audio with an uploaded file.

        Args:
            dialogue_id: Dialogue UUID.
            file_path: Path to uploaded audio file.

        Returns:
            Path to stored audio file.
        """
        dest_dir = self._storage_path / "audio" / dialogue_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / Path(file_path).name

        async with aiofiles.open(file_path, "rb") as src:
            content = await src.read()
        async with aiofiles.open(str(dest_path), "wb") as dst:
            await dst.write(content)

        return str(dest_path)

    async def adjust_params(
        self,
        input_path: str,
        *,
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
    ) -> str:
        """Adjust audio parameters.

        Args:
            input_path: Path to source audio.
            speed: Speed multiplier.
            pitch: Pitch shift in semitones.
            volume: Volume multiplier.

        Returns:
            Path to adjusted audio.
        """
        output_path = str(Path(input_path).with_stem(Path(input_path).stem + "_adjusted"))
        filters = []
        if speed != 1.0:
            filters.append(f"atempo={speed}")
        if pitch != 0.0:
            # Rubberband for pitch shifting
            filters.append(f"rubberband=pitch={2 ** (pitch / 12)}")
        if volume != 1.0:
            filters.append(f"volume={volume}")

        filter_str = ",".join(filters) if filters else "anull"
        cmd = f'ffmpeg -y -i "{input_path}" -af "{filter_str}" -c:a flac "{output_path}"'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def trim_silence(self, input_path: str, threshold_db: float = -40.0) -> str:
        """Trim silence from beginning and end of audio.

        Args:
            input_path: Path to source audio.
            threshold_db: Silence threshold in dB.

        Returns:
            Path to trimmed audio.
        """
        output_path = str(Path(input_path).with_stem(Path(input_path).stem + "_trimmed"))
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-af "silenceremove=start_periods=1:start_duration=0:start_threshold={threshold_db}dB:'
            f'stop_periods=1:stop_duration=0:stop_threshold={threshold_db}dB" '
            f'-c:a flac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def denoise(self, input_path: str) -> str:
        """Apply noise reduction to audio.

        Args:
            input_path: Path to source audio.

        Returns:
            Path to denoised audio.
        """
        output_path = str(Path(input_path).with_stem(Path(input_path).stem + "_denoised"))
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-af "highpass=f=200,lowpass=f=3000,afftdn=nf=-25" '
            f'-c:a flac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def adjust_timing(
        self,
        input_path: str,
        target_duration_sec: float,
    ) -> str:
        """Adjust audio to fit a target duration.

        Args:
            input_path: Path to source audio.
            target_duration_sec: Target duration in seconds.

        Returns:
            Path to timing-adjusted audio.
        """
        # Get current duration
        probe_cmd = (
            f'ffprobe -v error -show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 "{input_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            probe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        current_duration = float(stdout.decode().strip() or "0")

        if current_duration <= 0:
            return input_path

        speed_factor = current_duration / target_duration_sec
        return await self.adjust_params(input_path, speed=max(0.5, min(2.0, speed_factor)))

    async def batch_regenerate(
        self,
        dialogues: list[dict[str, Any]],
    ) -> list[bytes]:
        """Batch regenerate multiple dialogue audios.

        Args:
            dialogues: List of dicts with text, character_voice, emotion, params.

        Returns:
            List of audio bytes.
        """
        results: list[bytes] = []
        for d in dialogues:
            audio = await self.regenerate(
                dialogue_id=d.get("id", ""),
                text=d["text"],
                character_voice=d.get("character_voice"),
                emotion=d.get("emotion", "calm"),
                params=d.get("params"),
            )
            results.append(audio)
        return results

    async def batch_params(
        self,
        files: list[str],
        *,
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
    ) -> list[str]:
        """Batch adjust parameters for multiple audio files.

        Args:
            files: List of audio file paths.
            speed: Speed multiplier.
            pitch: Pitch shift in semitones.
            volume: Volume multiplier.

        Returns:
            List of adjusted audio file paths.
        """
        results: list[str] = []
        for f in files:
            adjusted = await self.adjust_params(f, speed=speed, pitch=pitch, volume=volume)
            results.append(adjusted)
        return results
