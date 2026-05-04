"""Health check router."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from api.config import settings
from api.routers import ApiResponse, success

router = APIRouter(prefix="/api/health", tags=["health"])

APP_VERSION = "0.1.0"


@router.get("", response_model=ApiResponse)
async def health_check() -> dict[str, Any]:
    """Basic API health check."""
    return success({
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/services", response_model=ApiResponse)
async def check_services() -> dict[str, Any]:
    """Check connectivity to dependent services (stub)."""
    # TODO: actual connectivity checks
    return success({
        "database": {"status": "unknown", "url": settings.database.postgres_url.split("@")[-1]},
        "redis": {"status": "unknown", "url": settings.redis.url},
        "comfyui": {"status": "unknown", "url": settings.comfyui.base_url},
        "dify": {"status": "unknown", "url": settings.dify.api_url},
    })


@router.get("/versions", response_model=ApiResponse)
async def get_versions() -> dict[str, Any]:
    """Return version info for all components."""
    return success({
        "api": APP_VERSION,
        "python": "3.11+",
        "fastapi": "0.115+",
        "sqlalchemy": "2.0+",
    })


@router.get("/storage", response_model=ApiResponse)
async def get_storage() -> dict[str, Any]:
    """Return storage usage info."""
    storage_path = settings.storage.local_path
    try:
        usage = shutil.disk_usage(storage_path)
        return success({
            "path": storage_path,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "usage_percent": round(usage.used / usage.total * 100, 1),
        })
    except FileNotFoundError:
        return success({
            "path": storage_path,
            "error": "Storage path not found",
        })
