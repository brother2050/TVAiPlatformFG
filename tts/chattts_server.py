"""ChatTTS synthesis server — FastAPI wrapper on port 8090.

Provides POST /synthesize for text-to-speech with emotion tags,
speaker sampling, and tunable generation parameters.
"""

from __future__ import annotations

import io
import logging
import tempfile
from enum import Enum
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger("chattts_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="ChatTTS Server", version="1.0.0")

# ---------------------------------------------------------------------------
# Lazy ChatTTS import — model loads on first request
# ---------------------------------------------------------------------------
_chat: object | None = None


def _get_chat() -> object:
    """Return a lazily-loaded ChatTTS instance."""
    global _chat  # noqa: PLW0603
    if _chat is None:
        import ChatTTS

        logger.info("Loading ChatTTS model …")
        _chat = ChatTTS.Chat()
        _chat.load_models(compile=False)
        logger.info("ChatTTS model ready.")
    return _chat


# ---------------------------------------------------------------------------
# Emotion presets — each maps to an oral / laugh / break token prefix
# ---------------------------------------------------------------------------
class Emotion(str, Enum):
    happy = "happy"
    sad = "sad"
    angry = "angry"
    fearful = "fearful"
    surprised = "surprised"
    calm = "calm"
    whisper = "whisper"
    neutral = "neutral"


_EMOTION_PREFIXES: dict[Emotion, str] = {
    Emotion.happy: "[oral_2][laugh_0]",
    Emotion.sad: "[oral_0][break_4]",
    Emotion.angry: "[oral_2][break_2]",
    Emotion.fearful: "[oral_1][break_6]",
    Emotion.surprised: "[oral_2][laugh_1]",
    Emotion.calm: "[oral_0]",
    Emotion.whisper: "[oral_0][break_2]",
    Emotion.neutral: "[oral_1]",
}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    spk_smp: str | None = Field(None, description="Speaker embedding seed string (hex-encoded)")
    temperature: float = Field(0.3, ge=0.0, le=1.0)
    top_p: float = Field(0.7, ge=0.0, le=1.0)
    top_k: int = Field(20, ge=0, le=100)
    emotion: Emotion = Field(Emotion.neutral, description="Emotion preset")
    format: str = Field("wav", pattern="^(wav|flac)$", description="Output audio format")


class HealthResponse(BaseModel):
    status: str = "ok"
    model_loaded: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(model_loaded=_chat is not None)


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest) -> Response:
    """Synthesize speech from text and return raw audio bytes."""
    chat = _get_chat()

    # Build prompt with emotion prefix
    prefix = _EMOTION_PREFIXES.get(req.emotion, "")
    prompt_text = f"{prefix}{req.text}" if prefix else req.text

    # Parse speaker seed
    params_infer_code: dict = {
        "temperature": req.temperature,
        "top_P": req.top_p,
        "top_K": req.top_k,
    }
    if req.spk_smp:
        try:
            spk_tensor = chat.sample_audio_speaker(req.spk_smp)
            params_infer_code["spk_emb"] = spk_tensor
        except Exception:
            logger.warning("Invalid spk_smp '%s', using random speaker", req.spk_smp)

    try:
        wavs = chat.infer([prompt_text], params_infer_code=params_infer_code)
    except Exception as exc:
        logger.exception("ChatTTS inference failed")
        raise HTTPException(status_code=500, detail=f"TTS inference failed: {exc}") from exc

    audio: np.ndarray = wavs[0]
    if audio.ndim > 1:
        audio = audio.squeeze()

    # Render to buffer
    buf = io.BytesIO()
    subtype = "PCM_16" if req.format == "wav" else "PCM_24"
    sf.write(buf, audio, 24000, format=req.format.upper(), subtype=subtype)
    buf.seek(0)

    media = "audio/wav" if req.format == "wav" else "audio/flac"
    return Response(content=buf.getvalue(), media_type=media)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
