"""Scenic style validation helpers for compliance checking."""

from typing import Any, Dict, List, Tuple
from pathlib import Path
from PIL import Image
import json


class StyleValidator:
    """Validates scenic style compliance and artifact completeness."""
    
    # Style requirements
    SCENIC_REQUIREMENTS = [
        "full color",
        "solid fills",
        "hand-painted",
        "theatrical",
        "clean outlines"
    ]
    
    # Style prohibitions
    STYLE_PROHIBITIONS = [
        "photorealism",
        "3d render",
        "photorealistic",
        "gradient",
        "blur",
        "airbrush",
        "glow",
        "watermark",
        "text",
        "logo"
    ]
    
    # Required artifacts
    REQUIRED_ARTIFACTS = [
        "final.png",
        "prompt.txt",
        "negative_prompt.txt",
        "brief.json",
        "generation_response.json"
    ]

    NEGATIVE_CONSTRAINT_HINTS = [
        "photorealism",
        "3d",
        "blur",
        "text",
        "logo",
        "watermark",
        "gradient",
        "glow",
        "airbrush",
    ]

    @staticmethod
    def validate_style_contract(prompt: str) -> Tuple[bool, List[str]]:
        """Validate that prompt text reflects the scenic style contract."""
        issues = []
        prompt_lower = prompt.lower()

        found_style = any(
            indicator in prompt_lower
            for indicator in ["theatrical", "scenic", "stage", "scenic design"]
        )
        if not found_style:
            issues.append("Prompt missing theatrical/scenic style indicators")

        for prohibition in StyleValidator.STYLE_PROHIBITIONS:
            if prohibition in prompt_lower:
                issues.append(f"Prompt contains prohibited term: {prohibition}")

        return len(issues) == 0, issues

    @staticmethod
    def validate_negative_constraints(negative_prompt: str) -> Tuple[bool, List[str]]:
        """Validate that negative prompt text enforces the required constraints."""
        issues = []
        negative_lower = negative_prompt.lower()

        if not negative_prompt or len(negative_prompt.strip()) < 10:
            return False, ["Negative prompt is missing or too brief"]

        matched = [
            hint for hint in StyleValidator.NEGATIVE_CONSTRAINT_HINTS if hint in negative_lower
        ]
        if len(matched) < 3:
            issues.append("Negative prompt is missing required scenic constraint coverage")

        return len(issues) == 0, issues
    
    @staticmethod
    def validate_scenic_style(
        prompt: str,
        negative_prompt: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that prompts contain scenic style guidance.
        
        Args:
            prompt: Final prompt used
            negative_prompt: Negative prompt used
            
        Returns:
            Tuple of (is_valid, issues)
        """
        style_valid, style_issues = StyleValidator.validate_style_contract(prompt)
        negative_valid, negative_issues = StyleValidator.validate_negative_constraints(negative_prompt)
        issues = [*style_issues, *negative_issues]
        return style_valid and negative_valid, issues
    
    @staticmethod
    def validate_artifact_completeness(
        output_dir: Path
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required artifacts exist.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            Tuple of (is_complete, missing_artifacts)
        """
        missing = []
        
        for artifact in StyleValidator.REQUIRED_ARTIFACTS:
            artifact_path = output_dir / artifact
            if not artifact_path.exists():
                missing.append(artifact)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_orientation_persistence(
        metadata_path: Path,
        validation_report_path: Path
    ) -> Tuple[bool, List[str]]:
        """
        Validate that orientation is properly persisted in metadata.
        
        Args:
            metadata_path: Path to generation metadata JSON
            validation_report_path: Path to validation report JSON
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        try:
            # Check metadata
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    if "orientation" not in metadata:
                        issues.append("Orientation missing from metadata")
            else:
                issues.append("Metadata file not found")
            
            # Check validation report
            if validation_report_path.exists():
                with open(validation_report_path) as f:
                    report = json.load(f)
                    if "orientation" not in report:
                        issues.append("Orientation missing from validation report")
                    elif not report.get("orientation_valid", True):
                        issues.append("Orientation marked as invalid in report")
            else:
                issues.append("Validation report not found")
        
        except Exception as e:
            issues.append(f"Error checking orientation persistence: {str(e)}")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_image_quality(
        image_path: Path
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate basic image quality metrics.
        
        Args:
            image_path: Path to generated image
            
        Returns:
            Tuple of (is_valid, metrics)
        """
        metrics = {
            "exists": False,
            "size": 0,
            "dimensions": None,
            "has_color": False,
            "file_format": None
        }
        
        try:
            if not image_path.exists():
                return False, metrics
            
            metrics["exists"] = True
            metrics["size"] = image_path.stat().st_size
            
            # Open image and check properties
            image = Image.open(image_path)
            metrics["dimensions"] = image.size
            metrics["file_format"] = image.format
            metrics["has_color"] = image.mode in ["RGB", "RGBA"]
            
            # Basic validation
            is_valid = (
                metrics["exists"] and
                metrics["size"] > 1000 and  # Minimum size in bytes
                metrics["dimensions"][0] > 100 and
                metrics["dimensions"][1] > 100 and
                metrics["has_color"]
            )
            
            return is_valid, metrics
        
        except Exception as e:
            metrics["error"] = str(e)
            return False, metrics
    
    @staticmethod
    def validate_output_folder(
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation of an output folder.
        
        Args:
            output_dir: Output directory to validate
            
        Returns:
            Validation report dictionary
        """
        report = {
            "folder": str(output_dir),
            "exists": output_dir.exists(),
            "artifacts_complete": False,
            "artifacts_valid": True,
            "image_valid": False,
            "orientation_persistent": False,
            "issues": []
        }
        
        if not output_dir.exists():
            report["issues"].append(f"Output folder does not exist: {output_dir}")
            return report
        
        # Check artifacts
        artifacts_complete, missing = StyleValidator.validate_artifact_completeness(output_dir)
        report["artifacts_complete"] = artifacts_complete
        if missing:
            report["issues"].extend([f"Missing: {m}" for m in missing])
        
        # Check image
        final_image = output_dir / "final.png"
        if final_image.exists():
            is_valid, metrics = StyleValidator.validate_image_quality(final_image)
            report["image_valid"] = is_valid
            if not is_valid:
                report["issues"].append("Final image failed quality validation")
        
        # Check orientation persistence
        metadata_path = output_dir / "generation_response.json"
        report_path = output_dir / "validation_report.json"
        orientation_valid, orientation_issues = StyleValidator.validate_orientation_persistence(
            metadata_path,
            report_path
        )
        report["orientation_persistent"] = orientation_valid
        report["issues"].extend(orientation_issues)
        
        return report
