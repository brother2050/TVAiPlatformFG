"""Video editing service.

Provides trimming, regeneration, keyframe replacement, motion adjustment,
speed control, transitions, color grading, filters, and stabilization.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiofiles

from api.services.comfyui_runner import ComfyUIClientAdapter


class VideoEditorService:
    """Service for editing video clips.

    Args:
        comfyui: ComfyUIClientAdapter for AI video operations.
        storage_path: Base storage directory.
    """

    def __init__(self, comfyui: ComfyUIClientAdapter, storage_path: str = "./storage") -> None:
        self._comfyui = comfyui
        self._storage_path = Path(storage_path)

    async def trim(
        self,
        input_path: str,
        start_sec: float,
        end_sec: float,
    ) -> str:
        """Trim a video clip.

        Args:
            input_path: Path to source video.
            start_sec: Start time in seconds.
            end_sec: End time in seconds.

        Returns:
            Path to trimmed video.
        """
        output_path = str(Path(input_path).with_stem(Path(input_path).stem + "_trimmed"))
        duration = end_sec - start_sec
        cmd = (
            f'ffmpeg -y -ss {start_sec} -i "{input_path}" '
            f'-t {duration} -c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def regenerate(
        self,
        shot_id: str,
        keyframe_path: str,
        motion_prompt: str = "",
        duration_sec: float = 4.0,
    ) -> dict[str, Any]:
        """Regenerate a video from a keyframe.

        Args:
            shot_id: Shot UUID.
            keyframe_path: Path to keyframe image.
            motion_prompt: Motion description.
            duration_sec: Target duration.

        Returns:
            Dict with 'video_path' and 'metadata'.
        """
        return await self._comfyui.generate_video(
            keyframe_path=keyframe_path,
            motion_prompt=motion_prompt,
            duration_sec=duration_sec,
        )

    async def replace_keyframe(
        self,
        shot_id: str,
        new_keyframe_path: str,
        motion_prompt: str = "",
        duration_sec: float = 4.0,
    ) -> dict[str, Any]:
        """Replace the keyframe and regenerate the video.

        Args:
            shot_id: Shot UUID.
            new_keyframe_path: Path to new keyframe.
            motion_prompt: Motion description.
            duration_sec: Target duration.

        Returns:
            Dict with 'video_path' and 'metadata'.
        """
        return await self.regenerate(
            shot_id=shot_id,
            keyframe_path=new_keyframe_path,
            motion_prompt=motion_prompt,
            duration_sec=duration_sec,
        )

    async def upload_replace(self, shot_id: str, file_path: str) -> str:
        """Replace video with an uploaded file.

        Args:
            shot_id: Shot UUID.
            file_path: Path to uploaded video.

        Returns:
            Path to stored video.
        """
        dest_dir = self._storage_path / "videos" / shot_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / Path(file_path).name

        async with aiofiles.open(file_path, "rb") as src:
            content = await src.read()
        async with aiofiles.open(str(dest_path), "wb") as dst:
            await dst.write(content)

        return str(dest_path)

    async def adjust_motion(self, video_path: str, motion_scale: float = 1.0) -> str:
        """Adjust motion intensity of a video.

        Args:
            video_path: Path to source video.
            motion_scale: Motion scale factor (0.5 = half speed motion, 2.0 = double).

        Returns:
            Path to adjusted video.
        """
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + "_motion"))
        # Adjust via speed filter (inverse relationship)
        speed = 1.0 / motion_scale
        cmd = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "setpts={1/speed}*PTS" -af "atempo={speed}" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def adjust_speed(self, video_path: str, speed: float = 1.0) -> str:
        """Adjust playback speed.

        Args:
            video_path: Path to source video.
            speed: Speed multiplier (2.0 = 2x faster).

        Returns:
            Path to speed-adjusted video.
        """
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + "_speed"))
        cmd = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "setpts={1/speed}*PTS" -af "atempo={min(2.0, max(0.5, speed))}" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def reverse(self, video_path: str) -> str:
        """Reverse a video.

        Args:
            video_path: Path to source video.

        Returns:
            Path to reversed video.
        """
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + "_reverse"))
        cmd = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf reverse -af areverse '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def set_transition(
        self,
        clip_a_path: str,
        clip_b_path: str,
        transition: str = "fade",
        duration_sec: float = 1.0,
    ) -> str:
        """Apply a transition between two clips.

        Args:
            clip_a_path: Path to first clip.
            clip_b_path: Path to second clip.
            transition: Transition type (fade/dissolve/wipe).
            duration_sec: Transition duration.

        Returns:
            Path to video with transition.
        """
        output_path = str(Path(clip_a_path).with_stem(Path(clip_a_path).stem + f"_{transition}"))
        # Simple cross-fade implementation
        cmd = (
            f'ffmpeg -y -i "{clip_a_path}" -i "{clip_b_path}" '
            f'-filter_complex "xfade=transition={transition}:duration={duration_sec}:offset=0" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def adjust_color(
        self,
        video_path: str,
        *,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> str:
        """Adjust color parameters of a video.

        Args:
            video_path: Path to source video.
            brightness: Brightness adjustment (-1.0 to 1.0).
            contrast: Contrast multiplier.
            saturation: Saturation multiplier.
            gamma: Gamma correction.

        Returns:
            Path to color-adjusted video.
        """
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + "_color"))
        cmd = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "eq=brightness={brightness}:contrast={contrast}:saturation={saturation}:gamma={gamma}" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def apply_filter(self, video_path: str, filter_name: str) -> str:
        """Apply a visual filter to a video.

        Args:
            video_path: Path to source video.
            filter_name: Filter name (cinematic/noir/vintage/warm/cool).

        Returns:
            Path to filtered video.
        """
        filter_map = {
            "cinematic": "eq=contrast=1.1:brightness=-0.05:saturation=0.9,curves=m='0/0 0.5/0.4 1/1'",
            "noir": "hue=s=0,eq=contrast=1.3:brightness=-0.1",
            "vintage": "colorbalance=rs=0.1:gs=-0.1:bs=-0.2,curves=vintage",
            "warm": "colorbalance=rs=0.15:gs=0.05:bs=-0.1",
            "cool": "colorbalance=rs=-0.1:gs=0.0:bs=0.15",
        }
        vf = filter_map.get(filter_name, "null")
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + f"_{filter_name}"))
        cmd = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "{vf}" -c:v libx264 -c:a aac "{output_path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return output_path

    async def stabilize(self, video_path: str, shakiness: int = 5) -> str:
        """Apply video stabilization.

        Args:
            video_path: Path to source video.
            shakiness: Shakiness detection level (1-10).

        Returns:
            Path to stabilized video.
        """
        output_path = str(Path(video_path).with_stem(Path(video_path).stem + "_stable"))
        # Two-pass stabilization
        transforms = str(Path(video_path).with_suffix(".trf"))
        cmd1 = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "vidstabdetect=shakiness={shakiness}:result={transforms}" '
            f'-f null -'
        )
        cmd2 = (
            f'ffmpeg -y -i "{video_path}" '
            f'-vf "vidstabtransform=input={transforms}:smoothing=10" '
            f'-c:v libx264 -c:a aac "{output_path}"'
        )
        for cmd in [cmd1, cmd2]:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
        # Cleanup transforms file
        Path(transforms).unlink(missing_ok=True)
        return output_path
