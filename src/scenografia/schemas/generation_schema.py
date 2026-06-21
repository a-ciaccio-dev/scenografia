"""
Generation request and response schemas for Scenografia.

Defines the core data structures for generation requests, response handling,
and mode/orientation tracking.
"""

from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field


class GenerationMode(str, Enum):
    """Supported generation modes."""
    DRAFT = "draft"
    STANDARD = "standard"
    PRODUCTION = "production"
    VECTOR_READY = "vector-ready"


class Orientation(str, Enum):
    """Supported output orientations."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"


class GenerationRequest(BaseModel):
    """Main request model for image generation."""
    
    # Input specification
    input_type: Literal["text", "sketch"]
    text_prompt: Optional[str] = Field(None, description="Text prompt for text-mode generation")
    sketch_path: Optional[str] = Field(None, description="Path to sketch file for sketch-mode generation")
    style_guidance: Optional[str] = Field(None, description="Style guidance for sketch mode")
    
    # Generation parameters
    mode: GenerationMode = GenerationMode.STANDARD
    orientation: Orientation = Field(description="Required output orientation")
    model_id: Optional[str] = Field(None, description="Optional override model ID")
    
    # Sketch mode options
    refine_sketch: bool = Field(False, description="Apply AI refinement to sketch")
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "text_prompt": "A mystical forest with ancient stone pillars",
                "mode": "standard",
                "orientation": "landscape"
            }
        }


class ImageGenerationResponse(BaseModel):
    """Response from OpenRouter image generation."""
    
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    error: Optional[str] = None
    model_used: str
    request_id: str
    
    class Config:
        arbitrary_types_allowed = True
