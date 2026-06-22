"""
Structured brief schemas for input normalization and briefing.

Represents the normalized output of the brief agent after processing
text prompts or sketch input into a structured generation brief.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from .generation_schema import Orientation, GenerationMode


class StructuredBrief(BaseModel):
    """
    Normalized and structured brief for image generation.
    
    This is the output of BriefAgent and is used by PromptEngineerAgent
    to compose the final prompt and by ImageGenerationAgent for provider
    request mapping.
    """
    
    # Core brief content
    scene_description: str = Field(
        description="Main scene description or prompt"
    )
    style_direction: Optional[str] = Field(
        None,
        description="Style guidance or direction"
    )
    
    # Mandatory orientation
    orientation: Orientation = Field(
        description="Required output orientation"
    )
    
    # Generation parameters
    generation_mode: GenerationMode = Field(
        GenerationMode.STANDARD,
        description="Generation mode"
    )
    
    # Metadata about the source
    source_type: str = Field(
        description="Source type: 'text' or 'sketch'"
    )
    source_file: Optional[str] = Field(
        None,
        description="Source file path if from file"
    )
    
    # Additional constraints and guidance
    scenic_requirements: List[str] = Field(
        default_factory=list,
        description="Specific scenic design requirements"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Generation constraints"
    )
    
    selected_style: Optional[str] = Field(
        "Default",
        description="Selected User Style name"
    )
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "scene_description": "Mystical forest clearing with ancient stone pillars",
                "style_direction": "theatrical fantasy",
                "orientation": "landscape",
                "generation_mode": "standard",
                "source_type": "text",
                "scenic_requirements": ["full color", "solid fills", "hand-painted look"],
                "constraints": ["no photorealism", "no gradients"]
            }
        }
