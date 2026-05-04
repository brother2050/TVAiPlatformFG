"""ComfyUI client adapter for image/video generation workflows.

Supports local, remote, and cloud ComfyUI instances.
All methods are async and use httpx.AsyncClient.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


@dataclass
class ComfyUIConfig:
    """Configuration for ComfyUI connection.

    Attributes:
        base_url: ComfyUI server URL (e.g. http://127.0.0.1:8188).
        ssl_verify: Whether to verify SSL certificates.
        timeout: Request timeout in seconds.
        upload_timeout: Upload timeout in seconds.
    """

    base_url: str = "http://127.0.0.1:8188"
    ssl_verify: bool = False
    timeout: int = 300
    upload_timeout: int = 120


class ComfyUIClientAdapter:
    """Async adapter for ComfyUI API.

    Provides high-level methods for character reference, keyframe,
    video, and inpainting generation via ComfyUI workflows.

    Args:
        config: ComfyUIConfig instance.
        workflows_dir: Path to workflow JSON templates directory.
    """

    def __init__(
        self,
        config: ComfyUIConfig,
        workflows_dir: str = "api/workflows",
    ) -> None:
        self._config = config
        self._base_url = config.base_url.rstrip("/")
        self._workflows_dir = Path(workflows_dir)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                verify=self._config.ssl_verify,
                timeout=httpx.Timeout(self._config.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _load_workflow(self, name: str) -> dict[str, Any]:
        """Load a workflow JSON template from disk.

        Args:
            name: Workflow filename (without .json).

        Returns:
            Parsed workflow JSON.

        Raises:
            FileNotFoundError: If workflow file doesn't exist.
        """
        path = self._workflows_dir / f"{name}.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Check if ComfyUI server is reachable.

        Returns:
            True if server responds, False otherwise.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/system_stats")
            return resp.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError):
            return False

    # ------------------------------------------------------------------
    # High-level generation methods
    # ------------------------------------------------------------------

    async def generate_character_reference(
        self,
        character_prompt: str,
        negative_prompt: str = "",
        seed: int | None = None,
        *,
        width: int = 1024,
        height: int = 1024,
    ) -> dict[str, Any]:
        """Generate a character reference sheet image.

        Args:
            character_prompt: Text description of the character.
            negative_prompt: What to avoid in the image.
            seed: Random seed for reproducibility.
            width: Output image width.
            height: Output image height.

        Returns:
            Dict with 'image_path' and 'metadata'.
        """
        workflow = self._load_workflow("character_reference_sheet")
        # Inject parameters into workflow nodes
        self._inject_params(workflow, {
            "positive_prompt": character_prompt,
            "negative_prompt": negative_prompt,
            "seed": seed or int(uuid.uuid4().int % (2**32)),
            "width": width,
            "height": height,
        })
        return await self._queue_workflow(workflow)

    async def generate_keyframe(
        self,
        visual_description: str,
        negative_prompt: str = "",
        character_reference_path: str | None = None,
        seed: int | None = None,
        *,
        width: int = 1280,
        height: int = 720,
    ) -> dict[str, Any]:
        """Generate a keyframe image for a shot.

        Args:
            visual_description: Visual description of the shot.
            negative_prompt: What to avoid.
            character_reference_path: Path to character reference image.
            seed: Random seed.
            width: Output width.
            height: Output height.

        Returns:
            Dict with 'image_path' and 'metadata'.
        """
        workflow = self._load_workflow("keyframe_generation")
        self._inject_params(workflow, {
            "positive_prompt": visual_description,
            "negative_prompt": negative_prompt,
            "seed": seed or int(uuid.uuid4().int % (2**32)),
            "width": width,
            "height": height,
            "reference_image": character_reference_path,
        })
        return await self._queue_workflow(workflow)

    async def generate_video(
        self,
        keyframe_path: str,
        motion_prompt: str = "",
        duration_sec: float = 4.0,
        fps: int = 24,
    ) -> dict[str, Any]:
        """Generate a video clip from a keyframe image (image-to-video).

        Args:
            keyframe_path: Path to the source keyframe image.
            motion_prompt: Description of desired motion.
            duration_sec: Target video duration in seconds.
            fps: Frames per second.

        Returns:
            Dict with 'video_path' and 'metadata'.
        """
        workflow = self._load_workflow("image_to_video_wan")
        self._inject_params(workflow, {
            "image_path": keyframe_path,
            "motion_prompt": motion_prompt,
            "duration_sec": duration_sec,
            "fps": fps,
        })
        return await self._queue_workflow(workflow)

    async def inpaint(
        self,
        image_path: str,
        mask_path: str,
        prompt: str,
        negative_prompt: str = "",
    ) -> dict[str, Any]:
        """Perform inpainting on a region of an image.

        Args:
            image_path: Path to the source image.
            mask_path: Path to the mask image (white = inpaint region).
            prompt: What to generate in the masked region.
            negative_prompt: What to avoid.

        Returns:
            Dict with 'image_path' and 'metadata'.
        """
        workflow = self._load_workflow("inpaint")
        self._inject_params(workflow, {
            "image_path": image_path,
            "mask_path": mask_path,
            "positive_prompt": prompt,
            "negative_prompt": negative_prompt,
        })
        return await self._queue_workflow(workflow)

    # ------------------------------------------------------------------
    # Low-level methods
    # ------------------------------------------------------------------

    def _inject_params(self, workflow: dict[str, Any], params: dict[str, Any]) -> None:
        """Inject parameters into workflow nodes by matching placeholder keys.

        Walks the workflow dict and replaces values that match param keys.

        Args:
            workflow: Workflow dict (modified in place).
            params: Parameters to inject.
        """
        if "prompt" in workflow:
            prompt = workflow["prompt"]
        elif "nodes" in workflow:
            prompt = workflow
        else:
            return

        def _walk(obj: Any) -> None:
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if isinstance(val, str) and val in params:
                        obj[key] = params[val]
                    elif isinstance(val, dict):
                        _walk(val)
                    elif isinstance(val, list):
                        for item in val:
                            _walk(item)

        _walk(prompt if isinstance(prompt, dict) else workflow)

    async def _queue_workflow(
        self,
        workflow: dict[str, Any],
        client_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit a workflow to ComfyUI queue.

        Args:
            workflow: The workflow JSON to execute.
            client_id: Optional client identifier.

        Returns:
            Dict with 'prompt_id' and 'status'.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        client = await self._get_client()
        payload = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id

        resp = await client.post("/prompt", json=payload)
        resp.raise_for_status()
        data = resp.json()

        prompt_id = data.get("prompt_id", "")
        return await self._wait_result(prompt_id)

    async def _wait_result(
        self,
        prompt_id: str,
        poll_interval: float = 2.0,
        max_wait: float | None = None,
    ) -> dict[str, Any]:
        """Poll ComfyUI until a workflow completes.

        Args:
            prompt_id: The prompt ID returned by _queue_workflow.
            poll_interval: Seconds between polls.
            max_wait: Maximum wait time (defaults to config timeout).

        Returns:
            Dict with 'image_path' or 'video_path' and 'metadata'.

        Raises:
            TimeoutError: If max_wait is exceeded.
            RuntimeError: If the workflow fails.
        """
        client = await self._get_client()
        deadline = max_wait or float(self._config.timeout)
        elapsed = 0.0

        while elapsed < deadline:
            resp = await client.get(f"/history/{prompt_id}")
            resp.raise_for_status()
            history = resp.json()

            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("completed", False):
                    outputs = entry.get("outputs", {})
                    return self._extract_outputs(outputs)
                if status.get("status_str") == "error":
                    msg = status.get("messages", "Unknown ComfyUI error")
                    raise RuntimeError(f"ComfyUI workflow failed: {msg}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"ComfyUI workflow {prompt_id} timed out after {deadline}s")

    def _extract_outputs(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Extract output file paths from ComfyUI history outputs.

        Args:
            outputs: The outputs dict from ComfyUI history.

        Returns:
            Dict with extracted paths and metadata.
        """
        result: dict[str, Any] = {"images": [], "videos": [], "metadata": {}}

        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    result["images"].append({
                        "filename": img.get("filename", ""),
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output"),
                    })
            if "gifs" in node_output:
                for gif in node_output["gifs"]:
                    result["videos"].append({
                        "filename": gif.get("filename", ""),
                        "subfolder": gif.get("subfolder", ""),
                        "type": gif.get("type", "output"),
                    })

        # For convenience, set primary paths
        if result["images"]:
            first = result["images"][0]
            result["image_path"] = f"{first['subfolder']}/{first['filename']}" if first["subfolder"] else first["filename"]
        if result["videos"]:
            first = result["videos"][0]
            result["video_path"] = f"{first['subfolder']}/{first['filename']}" if first["subfolder"] else first["filename"]

        return result
