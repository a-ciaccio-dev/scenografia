"""Provider-facing image generation agent and pipeline service re-exports."""

from typing import Union, Optional
from scenografia.config import Config
from scenografia.schemas.generation_schema import GenerationRequest, ImageGenerationResponse
from scenografia.schemas.brief_schema import StructuredBrief, PromptPackage
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.providers.base import BaseImageProvider
from scenografia.providers.factory import get_image_provider

# Re-export pipeline services for backward compatibility
from scenografia.services.text_generation_service import TextGenerationService
from scenografia.services.sketch_generation_service import SketchGenerationService


class ImageGenerationAgent:
    """Provider-facing image generation agent."""

    def __init__(self, client: Optional[Union[BaseImageProvider, OpenRouterClient]] = None):
        self.client = client if client is not None else get_image_provider()

    def generate(
        self,
        request: GenerationRequest,
        prompt_package: Union[PromptPackage, dict],
        brief: Union[StructuredBrief, dict],
        input_image_bytes: Optional[bytes] = None
    ) -> ImageGenerationResponse:
        """Send the final prompt package to the image generation provider."""
        model_id = Config.get_model_id(request.mode, request.model_id)
        response = self.client.generate_image(
            prompt=prompt_package["final_prompt"],
            negative_prompt=prompt_package["negative_prompt"],
            model_id=model_id,
            orientation=request.orientation,
            input_image_bytes=input_image_bytes,
        )

        if response.error:
            raise RuntimeError(response.error)

        if response.image_data is None and response.image_url:
            if hasattr(self.client, "fetch_image_from_url"):
                response.image_data = self.client.fetch_image_from_url(response.image_url)

        if not response.image_data:
            raise RuntimeError("Image generation did not return image bytes")

        return response


__all__ = [
    "ImageGenerationAgent",
    "TextGenerationService",
    "SketchGenerationService",
]
