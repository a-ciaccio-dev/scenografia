"""
Structured brief and prompt package schemas for input normalization and briefing.

Represents the normalized output of the brief agent after processing
text prompts or sketch input into a structured generation brief, as well as
the prompt package produced by the prompt engineer.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
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
        default="text",
        description="Source type: 'text' or 'sketch'"
    )
    input_source: Optional[str] = Field(
        None,
        description="Source alias: 'text' or 'sketch'"
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
    style_constraints: List[str] = Field(
        default_factory=list,
        description="Specific style constraints"
    )
    negative_constraints: List[str] = Field(
        default_factory=list,
        description="Specific negative constraints"
    )
    composition_guidance: List[str] = Field(
        default_factory=list,
        description="Composition guidance items"
    )
    
    style_guidance: Optional[str] = Field(
        None,
        description="Optional style guidance text"
    )
    selected_style: Optional[str] = Field(
        "Default",
        description="Selected User Style name"
    )
    
    # Sketch-specific fields
    processed_sketch_path: Optional[str] = Field(
        None,
        description="Path to processed sketch if source is sketch"
    )
    refinement_applied: bool = Field(
        False,
        description="Whether AI refinement was applied"
    )
    
    model_config = ConfigDict(
        use_enum_values=False,
        arbitrary_types_allowed=True,
        json_schema_extra={
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
    )

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


class PromptPackage(BaseModel):
    """
    Composed prompt package ready for image generation provider.
    
    This is the output of PromptEngineerAgent.
    """
    final_prompt: str = Field(description="Final composed prompt sent to provider")
    negative_prompt: str = Field(default="", description="Negative prompt constraints")
    orientation_applied: bool = Field(False, description="Whether orientation was applied in the prompt")

    model_config = ConfigDict(
        use_enum_values=False,
        arbitrary_types_allowed=True
    )

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)
