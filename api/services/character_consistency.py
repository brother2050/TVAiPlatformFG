"""Character consistency management service.

Handles multi-view reference generation, age variants,
consistency locking, and face similarity computation.
"""

from __future__ import annotations

from typing import Any

from api.services.comfyui_runner import ComfyUIClientAdapter


class CharacterConsistencyService:
    """Service for maintaining character visual consistency across episodes.

    Args:
        comfyui: ComfyUIClientAdapter for image generation.
    """

    def __init__(self, comfyui: ComfyUIClientAdapter) -> None:
        self._comfyui = comfyui

    async def generate_reference_sheet(
        self,
        character_appearance: dict[str, Any],
        character_body: dict[str, Any],
        *,
        views: list[str] | None = None,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate a multi-view character reference sheet.

        Produces front, side (3/4), and back views for consistent character rendering.

        Args:
            character_appearance: Appearance spec (face_shape, eye_color, etc.).
            character_body: Body spec (height, body_type, etc.).
            views: List of view angles to generate (default: front, 3/4, side, back).
            seed: Random seed for reproducibility.

        Returns:
            Dict with 'reference_images' mapping view_name → image_path.
        """
        views = views or ["front", "three_quarter", "side", "back"]
        prompt_parts = [
            f"Character with {character_appearance.get('face_shape', 'oval')} face, "
            f"{character_appearance.get('eye_color', 'brown')} eyes, "
            f"{character_appearance.get('hair_style', 'short')} {character_appearance.get('hair_color', 'black')} hair, "
            f"{character_appearance.get('skin_tone', 'medium')} skin",
        ]
        if character_appearance.get("distinctive_features"):
            features = ", ".join(character_appearance["distinctive_features"])
            prompt_parts.append(f"distinctive features: {features}")
        if character_body:
            prompt_parts.append(f"{character_body.get('body_type', 'average')} build")

        base_prompt = ". ".join(prompt_parts)
        reference_images: dict[str, str] = {}

        for view in views:
            view_prompt = f"{base_prompt}, {view} view, character reference sheet, consistent style, white background"
            result = await self._comfyui.generate_character_reference(
                character_prompt=view_prompt,
                seed=seed,
            )
            if result.get("image_path"):
                reference_images[view] = result["image_path"]

        return {"reference_images": reference_images, "seed": seed}

    async def generate_age_variant(
        self,
        base_reference_path: str,
        target_age: str,
        *,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate an age variant of a character.

        Args:
            base_reference_path: Path to the base character reference image.
            target_age: Target age description (e.g. "child", "teenager", "elderly").
            seed: Random seed.

        Returns:
            Dict with 'image_path' of the age variant.
        """
        prompt = f"Same character as reference, aged to {target_age}, maintain facial features, character consistency"
        return await self._comfyui.generate_keyframe(
            visual_description=prompt,
            character_reference_path=base_reference_path,
            seed=seed,
        )

    async def lock_consistency(
        self,
        character_id: str,
        reference_images: dict[str, str],
        seed: int,
        face_embedding: list[float],
    ) -> dict[str, Any]:
        """Lock consistency parameters for a character.

        Stores the reference images, seed, and face embedding
        so future generations can maintain visual consistency.

        Args:
            character_id: Character UUID.
            reference_images: Mapping of view → image path.
            seed: The locked random seed.
            face_embedding: 512-dim face embedding vector.

        Returns:
            Dict with locked parameters.
        """
        return {
            "character_id": character_id,
            "reference_images": reference_images,
            "consistency_seed": seed,
            "face_embedding": face_embedding,
            "locked": True,
        }

    async def face_similarity(
        self,
        embedding_a: list[float],
        embedding_b: list[float],
    ) -> float:
        """Compute cosine similarity between two face embeddings.

        Args:
            embedding_a: First face embedding (512-dim).
            embedding_b: Second face embedding (512-dim).

        Returns:
            Cosine similarity score (0.0–1.0).
        """
        if len(embedding_a) != len(embedding_b) or not embedding_a:
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        norm_a = sum(a * a for a in embedding_a) ** 0.5
        norm_b = sum(b * b for b in embedding_b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity))
