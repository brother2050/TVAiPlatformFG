"""Dify API client for LLM-powered script/dialogue/storyboard generation.

Supports both local (http://127.0.0.1:5001) and third-party cloud Dify deployments.
Uses httpx.AsyncClient with 120s timeout.
Template injection: merges template.example + project_settings.to_prompt_context() into requests.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from api.config import DifyConfig


class DifyClient:
    """Async client for Dify workflow/conversation APIs.

    Args:
        config: DifyConfig with api_url and api_key.
        timeout: Request timeout in seconds (default 120).
    """

    def __init__(self, config: DifyConfig, timeout: float = 120.0) -> None:
        self._base_url = config.api_url.rstrip("/")
        self._api_key = config.api_key
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # High-level methods
    # ------------------------------------------------------------------

    async def generate_script(
        self,
        template_example: dict[str, Any],
        project_settings_context: str,
        user_input: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a script by injecting JSON template + global settings.

        Args:
            template_example: The template's example JSON structure.
            project_settings_context: Serialized project settings context.
            user_input: User's creative prompt / request.
            conversation_id: Optional conversation ID for multi-turn.

        Returns:
            Parsed JSON response from Dify.
        """
        system_prompt = (
            "You are a professional screenwriter AI. "
            "Follow the JSON structure exactly as shown in the template.\n\n"
            f"## Template Structure\n```json\n{json.dumps(template_example, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## Project Settings\n{project_settings_context}\n\n"
            "Generate content following the template structure precisely."
        )
        return await self._call_conversation(
            query=user_input,
            system_prompt=system_prompt,
            conversation_id=conversation_id,
        )

    async def generate_dialogues(
        self,
        template_example: dict[str, Any],
        project_settings_context: str,
        scene_description: str,
        characters_context: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate dialogues by injecting dialogue template.

        Args:
            template_example: Dialogue template example.
            project_settings_context: Serialized project settings.
            scene_description: Description of the scene.
            characters_context: Character profiles context.
            conversation_id: Optional conversation ID.

        Returns:
            Parsed JSON response from Dify.
        """
        system_prompt = (
            "You are a dialogue writer AI. Generate natural, character-consistent dialogues.\n\n"
            f"## Dialogue Template\n```json\n{json.dumps(template_example, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## Project Settings\n{project_settings_context}\n\n"
            f"## Characters\n{characters_context}\n\n"
            "Generate dialogues matching each character's personality and voice."
        )
        query = f"Scene: {scene_description}\n\nGenerate dialogues for this scene."
        return await self._call_conversation(
            query=query,
            system_prompt=system_prompt,
            conversation_id=conversation_id,
        )

    async def generate_storyboard(
        self,
        template_example: dict[str, Any],
        project_settings_context: str,
        script_content: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate storyboard by injecting storyboard template.

        Args:
            template_example: Storyboard template example.
            project_settings_context: Serialized project settings.
            script_content: The script to break into shots.
            conversation_id: Optional conversation ID.

        Returns:
            Parsed JSON response from Dify.
        """
        system_prompt = (
            "You are a storyboard director AI. Break scripts into detailed shots.\n\n"
            f"## Storyboard Template\n```json\n{json.dumps(template_example, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## Project Settings\n{project_settings_context}\n\n"
            "Create detailed shot breakdowns with camera angles, movements, and timing."
        )
        query = f"Script:\n{script_content}\n\nBreak this into a detailed storyboard."
        return await self._call_conversation(
            query=query,
            system_prompt=system_prompt,
            conversation_id=conversation_id,
        )

    # ------------------------------------------------------------------
    # Low-level API methods
    # ------------------------------------------------------------------

    async def _call_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        *,
        user: str = "system",
    ) -> dict[str, Any]:
        """Execute a Dify workflow.

        Args:
            workflow_id: The workflow identifier.
            inputs: Input parameters for the workflow.
            user: User identifier.

        Returns:
            Workflow execution result.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        client = await self._get_client()
        resp = await client.post(
            f"/workflows/{workflow_id}/run",
            json={"inputs": inputs, "response_mode": "blocking", "user": user},
        )
        resp.raise_for_status()
        return resp.json()

    async def _call_conversation(
        self,
        query: str,
        system_prompt: str,
        *,
        conversation_id: str | None = None,
        user: str = "system",
    ) -> dict[str, Any]:
        """Send a chat message to Dify conversation API.

        Args:
            query: User message.
            system_prompt: System-level prompt with template and context.
            conversation_id: For multi-turn conversations.
            user: User identifier.

        Returns:
            Parsed response with generated content.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": user,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        # Inject system prompt via inputs
        payload["inputs"]["system_prompt"] = system_prompt

        resp = await client.post("/chat-messages", json=payload)
        resp.raise_for_status()
        data = resp.json()

        # Try to parse the answer as JSON
        answer = data.get("answer", "")
        try:
            return json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            return {"raw_answer": answer, "conversation_id": data.get("conversation_id")}
