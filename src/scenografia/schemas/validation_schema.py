"""
Validation and metadata schemas for generation runs.

Represents generation metadata and validation reports for traceability,
style compliance, and artifact completeness.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import AliasChoices, BaseModel, Field
from .generation_schema import Orientation, GenerationMode


class GenerationMetadata(BaseModel):
    """
    Complete metadata for a generation run.
    
    Captures all context about how an image was generated for reproducibility
    and audit purposes.
    """
    
    # Identification
    run_id: str = Field(description="Unique run identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Request information
    input_type: str = Field(description="'text' or 'sketch'")
    original_prompt: str = Field(description="Original input/prompt")
    orientation: Orientation = Field(description="Output orientation")
    generation_mode: GenerationMode = Field(description="Generation mode used")
    
    # Model and provider information
    model_id: str = Field(description="Model used for generation")
    provider: str = Field(default="openrouter", description="Provider used")
    
    # Processing details
    brief: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured brief used"
    )
    final_prompt: str = Field(description="Final prompt sent to provider")
    negative_prompt: str = Field(description="Negative constraints")
    
    # Outputs
    image_url: Optional[str] = None
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Artifact file paths"
    )
    
    # Style information
    style_name: Optional[str] = Field(None, description="Name of user style used")
    style_description: Optional[str] = Field(None, description="Description of user style used")
    style_prompt_additions: Optional[str] = Field(None, description="Style prompt additions used")
    style_negative_additions: Optional[str] = Field(None, description="Style negative additions used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationReport(BaseModel):
    """
    Style compliance and artifact completeness validation report.
    
    Produced by StyleComplianceAgent and used to verify output quality,
    scenic style compliance, and artifact completeness.
    """
    
    # Validation metadata
    report_id: str = Field(description="Report identifier")
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    run_id: str = Field(description="Associated generation run ID")
    
    # Orientation capture and validation
    orientation: Orientation = Field(description="Validated orientation from metadata")
    orientation_valid: bool = Field(True, description="Whether orientation is present and valid")
    
    # Scenic style and constraint compliance
    style_contract_applied: bool = Field(
        default=False,
        validation_alias=AliasChoices("style_contract_applied", "style_compliant"),
        description="Whether the scenic style contract was applied",
    )
    negative_constraints_applied: bool = Field(
        default=False,
        description="Whether the negative constraints were applied",
    )
    
    # Artifact completeness
    artifacts_complete: bool = Field(description="All required artifacts present")
    missing_artifacts: List[str] = Field(
        default_factory=list,
        description="Any missing required artifacts"
    )

    issues: List[str] = Field(
        default_factory=list,
        description="Any issues detected during validation",
    )
    
    # Validation details
    validation_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Detailed validation scores"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "report_id": "val_20260621_001",
                "run_id": "gen_20260621_001",
                "orientation": "landscape",
                "orientation_valid": True,
                "style_contract_applied": True,
                "negative_constraints_applied": True,
                "artifacts_complete": True,
                "missing_artifacts": [],
                "issues": [],
                "validation_scores": {
                    "color_coverage": 0.95,
                    "outline_clarity": 0.92
                }
            }
        }
