"""Backend service layer for TVAiPlatform.

All service classes are async and use dependency injection for configuration.
External service calls (Dify, ComfyUI, TTS) go through httpx.AsyncClient.
"""

from api.services.chattts_client import ChatTTSClient
from api.services.character_consistency import CharacterConsistencyService
from api.services.context_compressor import ContextCompressor
from api.services.comfyui_runner import ComfyUIClientAdapter, ComfyUIConfig
from api.services.dify_client import DifyClient
from api.services.audio_editor import AudioEditorService
from api.services.editor import TextEditorService
from api.services.ffmpeg_service import FFmpegService
from api.services.global_settings import GlobalSettingsService
from api.services.image_editor import ImageEditorService
from api.services.production_pipeline import ProductionPipeline
from api.services.script_service import ScriptService
from api.services.storage_optimizer import (
    AudioStorageOptimizer,
    ImageStorageOptimizer,
    StorageCleaner,
    VideoStorageOptimizer,
)
from api.services.subtitle_service import SubtitleService
from api.services.summary_service import SummaryService
from api.services.sync_engine import SyncEngine
from api.services.template_service import TemplateService
from api.services.tts_service import TTSService
from api.services.video_editor import VideoEditorService

__all__ = [
    "AudioEditorService",
    "CharacterConsistencyService",
    "ChatTTSClient",
    "ComfyUIClientAdapter",
    "ComfyUIConfig",
    "ContextCompressor",
    "DifyClient",
    "FFmpegService",
    "GlobalSettingsService",
    "ImageEditorService",
    "ProductionPipeline",
    "ScriptService",
    "StorageCleaner",
    "SubtitleService",
    "SummaryService",
    "SyncEngine",
    "TemplateService",
    "TextEditorService",
    "TTSService",
    "VideoEditorService",
    "AudioStorageOptimizer",
    "ImageStorageOptimizer",
    "VideoStorageOptimizer",
]
