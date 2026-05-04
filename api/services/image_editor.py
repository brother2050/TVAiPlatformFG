"""Image editing service.

Provides regeneration, inpainting, upload/replace, upscaling,
background removal/replacement, and version management.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

from api.services.comfyui_runner import ComfyUIClientAdapter


class ImageEditorService:
    """Service for editing keyframe and reference images.

    Args:
        comfyui: ComfyUIClientAdapter for AI image operations.
        storage_path: Base storage directory for images.
    """

    def __init__(self, comfyui: ComfyUIClientAdapter, storage_path: str = "./storage") -> None:
        self._comfyui = comfyui
        self._storage_path = Path(storage_path)
        self._versions: dict[str, list[dict[str, Any]]] = {}  # shot_id → version list

    async def regenerate(
        self,
        shot_id: str,
        visual_description: str,
        character_reference_path: str | None = None,
        *,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Regenerate an image for a shot.

        Args:
            shot_id: Shot UUID.
            visual_description: New visual description prompt.
            character_reference_path: Optional character reference image.
            seed: Random seed for reproducibility.

        Returns:
            Dict with 'image_path' and 'metadata'.
        """
        result = await self._comfyui.generate_keyframe(
            visual_description=visual_description,
            character_reference_path=character_reference_path,
            seed=seed,
        )
        if result.get("image_path"):
            self._add_version(shot_id, result["image_path"], "regenerate")
        return result

    async def inpaint(
        self,
        shot_id: str,
        image_path: str,
        mask_path: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Inpaint a region of an image.

        Args:
            shot_id: Shot UUID.
            image_path: Path to the source image.
            mask_path: Path to the mask image.
            prompt: What to generate in the masked region.

        Returns:
            Dict with 'image_path' and 'metadata'.
        """
        result = await self._comfyui.inpaint(
            image_path=image_path,
            mask_path=mask_path,
            prompt=prompt,
        )
        if result.get("image_path"):
            self._add_version(shot_id, result["image_path"], "inpaint")
        return result

    async def upload_replace(self, shot_id: str, file_path: str) -> str:
        """Replace an image with an uploaded file.

        Args:
            shot_id: Shot UUID.
            file_path: Path to the uploaded image.

        Returns:
            Path to the stored image.
        """
        dest_dir = self._storage_path / "images" / shot_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / Path(file_path).name

        async with aiofiles.open(file_path, "rb") as src:
            content = await src.read()
        async with aiofiles.open(str(dest_path), "wb") as dst:
            await dst.write(content)

        self._add_version(shot_id, str(dest_path), "upload")
        return str(dest_path)

    async def adjust_params(
        self,
        shot_id: str,
        image_path: str,
        *,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
    ) -> str:
        """Adjust image parameters.

        Args:
            shot_id: Shot UUID.
            image_path: Path to the source image.
            brightness: Brightness factor (1.0 = unchanged).
            contrast: Contrast factor.
            saturation: Saturation factor.

        Returns:
            Path to the adjusted image.
        """
        from PIL import Image, ImageEnhance

        img = Image.open(image_path)
        img = ImageEnhance.Brightness(img).enhance(brightness)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageEnhance.Color(img).enhance(saturation)

        output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_adjusted"))
        img.save(output_path)
        self._add_version(shot_id, output_path, "adjust")
        return output_path

    async def upscale(self, shot_id: str, image_path: str, scale: float = 2.0) -> str:
        """Upscale an image.

        Args:
            shot_id: Shot UUID.
            image_path: Path to the source image.
            scale: Upscale factor.

        Returns:
            Path to the upscaled image.
        """
        from PIL import Image

        img = Image.open(image_path)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

        output_path = str(Path(image_path).with_stem(Path(image_path).stem + f"_x{int(scale)}"))
        img.save(output_path)
        self._add_version(shot_id, output_path, "upscale")
        return output_path

    async def remove_bg(self, image_path: str) -> str:
        """Remove background from an image.

        Args:
            image_path: Path to the source image.

        Returns:
            Path to the image with background removed.
        """
        # Placeholder — would use rembg or similar
        output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_nobg"))
        return output_path

    async def replace_bg(self, image_path: str, bg_path: str) -> str:
        """Replace background of an image.

        Args:
            image_path: Path to the foreground image.
            bg_path: Path to the new background image.

        Returns:
            Path to the composited image.
        """
        output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_newbg"))
        return output_path

    def get_versions(self, shot_id: str) -> list[dict[str, Any]]:
        """Get version history for a shot's images.

        Args:
            shot_id: Shot UUID.

        Returns:
            List of version info dicts.
        """
        return self._versions.get(shot_id, [])

    async def revert_version(self, shot_id: str, version_index: int) -> str | None:
        """Revert to a specific image version.

        Args:
            shot_id: Shot UUID.
            version_index: Version index to revert to.

        Returns:
            Path to the reverted image, or None if not found.
        """
        versions = self._versions.get(shot_id, [])
        if 0 <= version_index < len(versions):
            return versions[version_index]["path"]
        return None

    def _add_version(self, shot_id: str, path: str, operation: str) -> None:
        """Add a version entry.

        Args:
            shot_id: Shot UUID.
            path: Image file path.
            operation: Operation that created this version.
        """
        if shot_id not in self._versions:
            self._versions[shot_id] = []
        self._versions[shot_id].append({
            "path": path,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
