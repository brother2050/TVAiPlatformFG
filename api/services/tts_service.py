"""TTS service with multi-engine support.

Supports engines: ChatTTS, CosyVoice, GPT-SoVITS, FishAudio, MiniMax.
Engine selection via configuration. Emotion parameter mapping included.
Output format: FLAC (22.05kHz).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

from api.config import TTSConfig


class TTSEngine(str, Enum):
    """Supported TTS engines."""

    CHATTTS = "chattts"
    COSYVOICE = "cosyvoice"
    GPT_SOVITS = "gpt-sovits"
    FISH_AUDIO = "fish-audio"
    MINIMAX = "minimax"


# Emotion → (speed_factor, pitch_shift_hz, energy_factor)
_EMOTION_MAP: dict[str, tuple[float, float, float]] = {
    "happy": (1.1, 20.0, 1.1),
    "sad": (0.9, -10.0, 0.85),
    "angry": (1.15, 15.0, 1.3),
    "fearful": (1.2, 25.0, 0.9),
    "surprised": (1.2, 30.0, 1.2),
    "calm": (0.95, -5.0, 0.9),
    "whisper": (0.85, 0.0, 0.5),
}


@dataclass
class EmotionParams:
    """Resolved TTS parameters for an emotion."""

    speed: float = 1.0
    pitch_shift: float = 0.0
    energy: float = 1.0


def resolve_emotion(emotion: str) -> EmotionParams:
    """Map an emotion string to TTS parameters.

    Args:
        emotion: One of happy/sad/angry/fearful/surprised/calm/whisper.

    Returns:
        EmotionParams with speed, pitch_shift, energy.
    """
    factors = _EMOTION_MAP.get(emotion, (1.0, 0.0, 1.0))
    return EmotionParams(speed=factors[0], pitch_shift=factors[1], energy=factors[2])


class TTSService:
    """Multi-engine TTS service.

    Args:
        config: TTSConfig with engine selection and engine-specific configs.
    """

    def __init__(self, config: TTSConfig) -> None:
        self._config = config
        self._engine = TTSEngine(config.engine)
        self._engine_configs = config.engines
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def synthesize(
        self,
        text: str,
        character_voice: dict[str, Any] | None = None,
        emotion: str = "calm",
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """Synthesize speech from text.

        Args:
            text: Text to speak.
            character_voice: Character voice spec (tone, speed, pitch).
            emotion: Emotion label for parameter mapping.
            params: Additional engine-specific parameters.

        Returns:
            Raw audio bytes (FLAC format, 22.05kHz).
        """
        emotion_params = resolve_emotion(emotion)
        merged_params = {
            "speed": emotion_params.speed,
            "pitch_shift": emotion_params.pitch_shift,
            "energy": emotion_params.energy,
            **(params or {}),
        }
        if character_voice:
            merged_params.setdefault("tone", character_voice.get("tone", ""))
            merged_params.setdefault("base_speed", character_voice.get("speed", "normal"))
            merged_params.setdefault("base_pitch", character_voice.get("pitch", "normal"))

        engine = merged_params.pop("engine", self._engine.value)

        if engine == TTSEngine.CHATTTS:
            return await self._synthesize_chattts(text, merged_params)
        elif engine == TTSEngine.COSYVOICE:
            return await self._synthesize_cosyvoice(text, merged_params)
        elif engine == TTSEngine.GPT_SOVITS:
            return await self._synthesize_gpt_sovits(text, merged_params)
        elif engine == TTSEngine.FISH_AUDIO:
            return await self._synthesize_fish_audio(text, merged_params)
        elif engine == TTSEngine.MINIMAX:
            return await self._synthesize_minimax(text, merged_params)
        else:
            raise ValueError(f"Unsupported TTS engine: {engine}")

    async def _synthesize_chattts(self, text: str, params: dict[str, Any]) -> bytes:
        """Synthesize via ChatTTS engine.

        Args:
            text: Text to synthesize.
            params: Merged parameters.

        Returns:
            Audio bytes in FLAC format.
        """
        cfg = self._engine_configs.get("chattts", {})
        client = await self._get_client()
        resp = await client.post(
            cfg.get("api_url", "http://127.0.0.1:5000/tts"),
            json={
                "text": text,
                "temperature": params.get("temperature", 0.3),
                "top_p": params.get("top_p", 0.7),
                "top_k": params.get("top_k", 20),
                "speed": params.get("speed", 1.0),
            },
        )
        resp.raise_for_status()
        return resp.content

    async def _synthesize_cosyvoice(self, text: str, params: dict[str, Any]) -> bytes:
        """Synthesize via CosyVoice engine.

        Args:
            text: Text to synthesize.
            params: Merged parameters.

        Returns:
            Audio bytes in FLAC format.
        """
        cfg = self._engine_configs.get("cosyvoice", {})
        client = await self._get_client()
        resp = await client.post(
            cfg.get("api_url", "http://127.0.0.1:5002/tts"),
            json={
                "text": text,
                "speaker": params.get("tone", "default"),
                "speed": params.get("speed", 1.0),
            },
        )
        resp.raise_for_status()
        return resp.content

    async def _synthesize_gpt_sovits(self, text: str, params: dict[str, Any]) -> bytes:
        """Synthesize via GPT-SoVITS engine.

        Args:
            text: Text to synthesize.
            params: Merged parameters.

        Returns:
            Audio bytes in FLAC format.
        """
        cfg = self._engine_configs.get("gpt-sovits", {})
        client = await self._get_client()
        resp = await client.post(
            cfg.get("api_url", "http://127.0.0.1:9880/tts"),
            json={
                "text": text,
                "text_language": params.get("language", "zh"),
                "refer_audio_path": params.get("reference_audio", ""),
                "prompt_text": params.get("prompt_text", ""),
                "speed": params.get("speed", 1.0),
            },
        )
        resp.raise_for_status()
        return resp.content

    async def _synthesize_fish_audio(self, text: str, params: dict[str, Any]) -> bytes:
        """Synthesize via FishAudio engine.

        Args:
            text: Text to synthesize.
            params: Merged parameters.

        Returns:
            Audio bytes in FLAC format.
        """
        cfg = self._engine_configs.get("fish-audio", {})
        client = await self._get_client()
        resp = await client.post(
            cfg.get("api_url", "https://api.fish.audio/v1/tts"),
            headers={"Authorization": f"Bearer {cfg.get('api_key', '')}"},
            json={
                "text": text,
                "reference_id": params.get("voice_id", cfg.get("voice_id", "")),
                "format": "flac",
                "mp3_bitrate": 128,
                "normalize": True,
            },
        )
        resp.raise_for_status()
        return resp.content

    async def _synthesize_minimax(self, text: str, params: dict[str, Any]) -> bytes:
        """Synthesize via MiniMax engine.

        Args:
            text: Text to synthesize.
            params: Merged parameters.

        Returns:
            Audio bytes in FLAC format.
        """
        cfg = self._engine_configs.get("minimax", {})
        client = await self._get_client()
        resp = await client.post(
            cfg.get("api_url", "https://api.minimax.chat/v1/t2a_v2"),
            headers={"Authorization": f"Bearer {cfg.get('api_key', '')}"},
            json={
                "model": "speech-01-turbo",
                "text": text,
                "voice_setting": {
                    "voice_id": params.get("voice_id", cfg.get("voice_id", "")),
                    "speed": params.get("speed", 1.0),
                    "vol": params.get("energy", 1.0),
                    "pitch": params.get("pitch_shift", 0),
                },
                "audio_setting": {
                    "format": "flac",
                    "sample_rate": 22050,
                },
            },
        )
        resp.raise_for_status()
        return resp.content
