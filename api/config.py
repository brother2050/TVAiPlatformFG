"""Application configuration management using pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Sub-config models
# ---------------------------------------------------------------------------

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    api_port: int = 8000
    web_port: int = 3100


class ComfyUIConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8188"
    timeout: int = 300
    upload_timeout: int = 120
    ssl_verify: bool = False


class DifyConfig(BaseModel):
    api_url: str = "http://127.0.0.1:80/v1"
    api_key: str = ""


class TTSEngineConfig(BaseModel):
    voice: str = ""
    rate: str = "+0%"
    pitch: str = "+0Hz"
    api_url: str = ""
    api_key: str = ""
    voice_id: str = ""


class TTSConfig(BaseModel):
    engine: str = "edge-tts"
    engines: dict[str, dict[str, Any]] = Field(default_factory=dict)


class DatabaseConfig(BaseModel):
    type: str = "postgres"
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/tvai"
    pool_size: int = 20
    max_overflow: int = 10


class RedisConfig(BaseModel):
    url: str = "redis://127.0.0.1:6379/0"


class StorageConfig(BaseModel):
    type: str = "local"
    local_path: str = "./storage"
    image_format: str = "webp"
    image_quality: int = 85
    video_format: str = "mp4"
    audio_format: str = "wav"
    max_upload_size_mb: int = 100


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------

def _load_yaml_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load YAML config file, returning empty dict if not found."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    return {}


class AppConfig(BaseSettings):
    """Root application configuration.

    Reads from config.yaml first, then overlays environment variables.
    Environment variables override YAML values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    comfyui: ComfyUIConfig = Field(default_factory=ComfyUIConfig)
    dify: DifyConfig = Field(default_factory=DifyConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)


def load_config(yaml_path: str = "config.yaml") -> AppConfig:
    """Create AppConfig by merging YAML file with env vars."""
    yaml_data = _load_yaml_config(yaml_path)
    # Resolve ${VAR} placeholders in YAML
    resolved = _resolve_env_placeholders(yaml_data)
    return AppConfig(**resolved)


def _resolve_env_placeholders(obj: Any) -> Any:
    """Recursively resolve ${VAR} placeholders in config values."""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.environ.get(var_name, "")
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_placeholders(v) for v in obj]
    return obj


# Singleton config instance
settings = load_config()
