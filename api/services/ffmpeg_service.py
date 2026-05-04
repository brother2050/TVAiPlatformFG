"""FFmpeg composition service.

Handles multi-track mixing, video encoding, subtitle burning,
clip concatenation, transitions, and final encoding.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any


class FFmpegService:
    """Service for FFmpeg-based media composition.

    Args:
        storage_path: Base storage directory.
    """

    def __init__(self, storage_path: str = "./storage") -> None:
        self._storage_path = Path(storage_path)

    async def composite(
        self,
        video_path: str,
        output_path: str,
        *,
        voice_path: str | None = None,
        bgm_path: str | None = None,
        sfx_path: str | None = None,
        subtitle_path: str | None = None,
        voice_volume: float = 1.0,
        bgm_volume: float = 0.3,
        sfx_volume: float = 0.8,
        subtitle_style: str | None = None,
    ) -> str:
        """Composite video with multiple audio tracks and subtitles.

        Args:
            video_path: Path to source video.
            output_path: Path for output video.
            voice_path: Path to voice-over audio.
            bgm_path: Path to background music.
            sfx_path: Path to sound effects.
            subtitle_path: Path to SRT/ASS subtitle file.
            voice_volume: Voice track volume.
            bgm_volume: BGM track volume.
            sfx_volume: SFX track volume.
            subtitle_style: ASS subtitle style override.

        Returns:
            Path to composited video.
        """
        inputs = [f'-i "{video_path}"']
        filter_parts: list[str] = []
        audio_inputs = 1  # video has audio stream

        if voice_path:
            inputs.append(f'-i "{voice_path}"')
        if bgm_path:
            inputs.append(f'-i "{bgm_path}"')
        if sfx_path:
            inputs.append(f'-i "{sfx_path}"')

        # Build audio mixing filter
        audio_mix_parts: list[str] = []
        input_idx = 1  # audio inputs start at index 1

        if voice_path:
            filter_parts.append(f"[{input_idx}:a]volume={voice_volume}[voice]")
            audio_mix_parts.append("[voice]")
            input_idx += 1
        if bgm_path:
            filter_parts.append(f"[{input_idx}:a]volume={bgm_volume}[bgm]")
            audio_mix_parts.append("[bgm]")
            input_idx += 1
        if sfx_path:
            filter_parts.append(f"[{input_idx}:a]volume={sfx_volume}[sfx]")
            audio_mix_parts.append("[sfx]")
            input_idx += 1

        if len(audio_mix_parts) > 1:
            mix_inputs = "".join(audio_mix_parts)
            filter_parts.append(f"{mix_inputs}amix=inputs={len(audio_mix_parts)}:duration=longest[aout]")
            audio_map = "[aout]"
        elif audio_mix_parts:
            audio_map = audio_mix_parts[0]
        else:
            audio_map = "0:a"

        # Subtitle burning
        video_map = "0:v"
        if subtitle_path:
            sub_ext = Path(subtitle_path).suffix.lower()
            if sub_ext == ".ass":
                filter_parts.append(f"[0:v]ass={subtitle_path}[vout]")
            else:
                filter_parts.append(f"[0:v]subtitles={subtitle_path}[vout]")
            video_map = "[vout]"

        # Build command
        filter_str = ";".join(filter_parts) if filter_parts else None
        cmd_parts = ['ffmpeg -y']
        cmd_parts.extend(inputs)
        if filter_str:
            cmd_parts.append(f'-filter_complex "{filter_str}"')
        cmd_parts.append(f'-map "{video_map}" -map "{audio_map}"')
        cmd_parts.append('-c:v libx264 -c:a aac -b:a 192k')
        cmd_parts.append(f'"{output_path}"')

        cmd = " ".join(cmd_parts)
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def concat_clips(
        self,
        clip_paths: list[str],
        output_path: str,
        *,
        method: str = "demuxer",
    ) -> str:
        """Concatenate multiple video clips.

        Args:
            clip_paths: List of video file paths.
            output_path: Output file path.
            method: Concat method (demuxer/filter).

        Returns:
            Path to concatenated video.
        """
        if method == "demuxer":
            # Write concat list
            list_path = str(Path(output_path).with_suffix(".txt"))
            async with __import__("aiofiles").open(list_path, "w") as f:
                for clip in clip_paths:
                    await f.write(f"file '{clip}'\n")

            cmd = (
                f'ffmpeg -y -f concat -safe 0 -i "{list_path}" '
                f'-c copy "{output_path}"'
            )
        else:
            # Filter-based concat
            inputs = " ".join(f'-i "{c}"' for c in clip_paths)
            n = len(clip_paths)
            streams = "".join(f"[{i}:v][{i}:a]" for i in range(n))
            cmd = (
                f'ffmpeg -y {inputs} '
                f'-filter_complex "{streams}concat=n={n}:v=1:a=1[outv][outa]" '
                f'-map "[outv]" -map "[outa]" '
                f'-c:v libx264 -c:a aac "{output_path}"'
            )

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def add_transitions(
        self,
        clips: list[str],
        output_path: str,
        *,
        transition: str = "fade",
        duration_sec: float = 1.0,
    ) -> str:
        """Add transitions between clips.

        Args:
            clips: List of video clip paths.
            output_path: Output file path.
            transition: Transition type (fade/dissolve/wipe).
            duration_sec: Transition duration.

        Returns:
            Path to video with transitions.
        """
        if len(clips) < 2:
            return clips[0] if clips else output_path

        # Build xfade filter chain
        inputs = " ".join(f'-i "{c}"' for c in clips)
        filter_parts: list[str] = []
        prev_label = "[0:v]"

        for i in range(1, len(clips)):
            # Calculate offset (end of previous clip minus transition duration)
            offset_cmd = (
                f'ffprobe -v error -show_entries format=duration '
                f'-of default=noprint_wrappers=1:nokey=1 "{clips[i-1]}"'
            )
            proc = await asyncio.create_subprocess_shell(
                offset_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            try:
                clip_dur = float(stdout.decode().strip())
            except (ValueError, TypeError):
                clip_dur = 4.0

            offset = max(0, clip_dur - duration_sec)
            out_label = f"[v{i}]" if i < len(clips) - 1 else "[outv]"
            filter_parts.append(
                f"{prev_label}[{i}:v]xfade=transition={transition}:duration={duration_sec}:offset={offset}{out_label}"
            )
            prev_label = out_label

        filter_str = ";".join(filter_parts)

        # Audio crossfade
        audio_parts: list[str] = []
        prev_audio = "[0:a]"
        for i in range(1, len(clips)):
            out_a = f"[a{i}]" if i < len(clips) - 1 else "[outa]"
            audio_parts.append(
                f"{prev_audio}[{i}:a]acrossfade=d={duration_sec}:c1=tri:c2=tri{out_a}"
            )
            prev_audio = out_a

        if audio_parts:
            filter_str += ";" + ";".join(audio_parts)

        cmd = (
            f'ffmpeg -y {inputs} '
            f'-filter_complex "{filter_str}" '
            f'-map "[outv]" -map "[outa]" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def encode_final(
        self,
        input_path: str,
        output_path: str,
        *,
        resolution: str = "1080p",
        fps: int = 30,
        codec: str = "libx264",
        crf: int = 18,
        preset: str = "slow",
        audio_codec: str = "aac",
        audio_bitrate: str = "192k",
    ) -> str:
        """Final encoding with quality presets.

        Args:
            input_path: Path to source video.
            output_path: Path for output.
            resolution: Target resolution (720p/1080p/4k).
            fps: Target frame rate.
            codec: Video codec.
            crf: Constant Rate Factor.
            preset: Encoding preset.
            audio_codec: Audio codec.
            audio_bitrate: Audio bitrate.

        Returns:
            Path to encoded video.
        """
        res_map = {"720p": "1280:720", "1080p": "1920:1080", "4k": "3840:2160"}
        scale = res_map.get(resolution, "1920:1080")

        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-vf "scale={scale}" '
            f'-r {fps} '
            f'-c:v {codec} -crf {crf} -preset {preset} '
            f'-c:a {audio_codec} -b:a {audio_bitrate} '
            f'-movflags +faststart '
            f'"{output_path}"'
        )

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path
