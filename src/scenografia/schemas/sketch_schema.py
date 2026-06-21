"""
Sketch interpretation schemas for preprocessing and sketch analysis.

Represents the output of SketchInterpreterAgent after local preprocessing
and optional AI refinement.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SketchInterpretation(BaseModel):
    """
    Result of sketch preprocessing and interpretation.
    
    Produced by SketchInterpreterAgent after local black-and-white
    preprocessing and optional AI vision refinement.
    """
    
    # Processed sketch information
    processed_sketch_path: str = Field(
        description="Path to processed sketch PNG"
    )
    
    # Interpretation results
    scene_elements: list[str] = Field(
        default_factory=list,
        description="Identified scene elements from sketch"
    )
    composition_notes: Optional[str] = Field(
        None,
        description="Notes about composition and layout"
    )
    
    # AI refinement results (if enabled)
    refinement_applied: bool = Field(
        False,
        description="Whether AI refinement was applied"
    )
    refinement_description: Optional[str] = Field(
        None,
        description="Description of refinement applied"
    )
    
    # Preprocessing details
    preprocessing_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Details about preprocessing steps"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "processed_sketch_path": "output/2026-06-21_1430_forest/processed_sketch.png",
                "scene_elements": ["pillars", "forest canopy", "ground level"],
                "composition_notes": "Vertical arrangement with focal point center",
                "refinement_applied": False,
                "preprocessing_details": {
                    "original_size": [640, 480],
                    "processed_size": [640, 480],
                    "contrast_adjusted": True
                }
            }
        }
