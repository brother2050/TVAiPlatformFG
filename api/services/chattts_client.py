"""ChatTTS dedicated client with emotion tag support.

Supports emotion tags like [laugh], [uv_break] in text.
"""

from __future__ import annotations

from typing import Any

import httpx


class ChatTTSClient:
    """Dedicated client for ChatTTS API.

    Args:
        api_url: ChatTTS server URL.
        timeout: Request timeout in seconds.
    """

    def __init__(self, api_url: str = "http://127.0.0.1:5000", timeout: float = 120.0) -> None:
        self._api_url = api_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def synthesize(
        self,
        text: str,
        spk_smp: str | None = None,
        temperature: float = 0.3,
        top_p: float = 0.7,
        top_k: int = 20,
        *,
        speed: float = 1.0,
        oral: int = 2,
        laugh: int = 0,
        break_mode: int = 1,
    ) -> bytes:
        """Synthesize speech from text with ChatTTS.

        Supports emotion tags embedded in text:
        - [laugh] — insert laughter
        - [uv_break] — insert a break
        - [oral_0] to [oral_9] — oral emphasis level
        - [laugh_0] to [laugh_9] — laugh intensity
        - [break_0] to [break_9] — break duration

        Args:
            text: Text to synthesize (may include emotion tags).
            spk_smp: Speaker embedding/sample ID (None for random).
            temperature: Sampling temperature (0.0–1.0).
            top_p: Top-p sampling parameter.
            top_k: Top-k sampling parameter.
            speed: Speech speed multiplier.
            oral: Oral emphasis level (0–9).
            laugh: Laugh intensity (0–9).
            break_mode: Break handling mode.

        Returns:
            Raw audio bytes (WAV format from ChatTTS).
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "text": text,
            "temperature": temperature,
            "top_P": top_p,
            "top_K": top_k,
            "speed": speed,
            "oral": oral,
            "laugh": laugh,
            "break_mode": break_mode,
        }
        if spk_smp is not None:
            payload["spk_smp"] = spk_smp

        resp = await client.post(f"{self._api_url}/tts", json=payload)
        resp.raise_for_status()
        return resp.content

    async def batch_synthesize(
        self,
        texts: list[str],
        spk_smp: str | None = None,
        temperature: float = 0.3,
        top_p: float = 0.7,
        top_k: int = 20,
    ) -> list[bytes]:
        """Batch synthesize multiple texts with the same voice.

        Args:
            texts: List of texts to synthesize.
            spk_smp: Speaker embedding/sample ID.
            temperature: Sampling temperature.
            top_p: Top-p sampling parameter.
            top_k: Top-k sampling parameter.

        Returns:
            List of audio bytes, one per input text.
        """
        results: list[bytes] = []
        for text in texts:
            audio = await self.synthesize(
                text=text,
                spk_smp=spk_smp,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
            )
            results.append(audio)
        return results

    async def get_speakers(self) -> list[dict[str, Any]]:
        """List available speaker embeddings.

        Returns:
            List of speaker info dicts.
        """
        client = await self._get_client()
        resp = await client.get(f"{self._api_url}/speakers")
        resp.raise_for_status()
        return resp.json()
