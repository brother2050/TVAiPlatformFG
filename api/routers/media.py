"""Media preview router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from api.routers import ApiResponse, success

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{path:path}/preview", response_model=ApiResponse)
async def preview_media(path: str) -> dict[str, Any]:
    """Return a preview URL for a media asset.

    In local mode, the asset is served via the static file mount at /api/media.
    In remote/cloud mode, a signed URL would be generated.
    """
    preview_url = f"/api/media/{path}"
    return success({"url": preview_url, "path": path})
