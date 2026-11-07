"""
Abstract protocols and base interfaces for AI text and image generation providers.
"""

from typing import Protocol, Optional, runtime_checkable
from scenografia.schemas.generation_schema import Orientation, ImageGenerationResponse


@runtime_checkable
class BaseImageProvider(Protocol):
    """Protocol for image generation providers."""

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: Optional[str] = None,
        orientation: Orientation = Orientation.LANDSCAPE,
        input_image_bytes: Optional[bytes] = None,
    ) -> ImageGenerationResponse:
        """
        Generate an image from prompt and orientation parameters.
        
        Args:
            prompt: Main scene prompt
            negative_prompt: Style constraints to avoid
            model_id: Model identifier (optional)
            orientation: Landscape, portrait, or square
            input_image_bytes: Optional image bytes for img2img refinement
            
        Returns:
            ImageGenerationResponse containing bytes or error
        """
        ...


@runtime_checkable
class BaseTextProvider(Protocol):
    """Protocol for text / LLM generation providers."""

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """
        Generate text response from prompt and optional vision image.
        
        Args:
            prompt: User message prompt
            system_instruction: Persona and formatting instructions
            model_id: Model identifier (optional)
            image_bytes: Optional image bytes for multimodal Vision analysis
            
        Returns:
            Generated text string
        """
        ...
