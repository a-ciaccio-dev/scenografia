"""
OpenRouter provider implementing BaseImageProvider and BaseTextProvider.
"""

from typing import Optional
from scenografia.schemas.generation_schema import Orientation, ImageGenerationResponse
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.providers.base import BaseImageProvider, BaseTextProvider


class OpenRouterProvider(BaseImageProvider, BaseTextProvider):
    """Provider adapter using OpenRouterClient."""

    def __init__(self, client: Optional[OpenRouterClient] = None):
        self.client = client or OpenRouterClient()

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: Optional[str] = None,
        orientation: Orientation = Orientation.LANDSCAPE,
        input_image_bytes: Optional[bytes] = None,
    ) -> ImageGenerationResponse:
        """Delegate image generation to OpenRouterClient."""
        effective_model = model_id or "google/gemini-2.5-flash-image"
        return self.client.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            model_id=effective_model,
            orientation=orientation,
            input_image_bytes=input_image_bytes,
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """Delegate text generation to OpenRouterClient."""
        effective_model = model_id or "google/gemini-2.5-flash"
        return self.client.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            model_id=effective_model,
            image_bytes=image_bytes,
        )
