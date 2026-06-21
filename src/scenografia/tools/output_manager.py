"""
Output management and artifact persistence.

Handles timestamped output directory creation and writing of all required
generation artifacts for reproducibility and traceability.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import re
from PIL import Image
from ..config import Config
from ..schemas.generation_schema import Orientation
from ..schemas.validation_schema import GenerationMetadata, ValidationReport
from .style_validator import StyleValidator


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
        
    Returns:
        Slugified text
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug[:50]  # Limit length


class OutputManager:
    """Manages output directory structure and artifact persistence."""

    @staticmethod
    def persist_text_run(
        brief: Dict[str, Any],
        prompt_package: Dict[str, Any],
        response: Any,
        validation_report: ValidationReport,
        metadata: GenerationMetadata,
        output_dir: Optional[Path] = None,
        processed_sketch_path: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Persist artifacts for a text-mode generation run."""
        output_dir = output_dir or OutputManager.create_output_directory(brief["scene_description"])
        artifacts = OutputManager.save_generation_artifacts(
            output_dir=output_dir,
            final_image_bytes=response.image_data,
            final_prompt=prompt_package["final_prompt"],
            negative_prompt=prompt_package["negative_prompt"],
            brief_dict=brief,
            metadata=metadata,
            processed_sketch_path=processed_sketch_path,
        )
        finalized_report = OutputManager.finalize_validation_report(output_dir, validation_report)
        artifacts["validation_report.json"] = OutputManager.save_validation_report(
            output_dir,
            finalized_report,
        )

        metadata.artifacts = {name: str(path) for name, path in artifacts.items()}
        OutputManager.save_json_artifact(
            output_dir,
            "generation_response.json",
            metadata,
        )

        return {
            "output_dir": output_dir,
            "image_path": artifacts["final.png"],
            "prompt_path": artifacts["prompt.txt"],
            "negative_prompt_path": artifacts["negative_prompt.txt"],
            "brief_path": artifacts["brief.json"],
            "metadata_path": output_dir / "generation_response.json",
            "validation_path": artifacts["validation_report.json"],
        }

    @staticmethod
    def finalize_validation_report(
        output_dir: Path,
        report: ValidationReport,
    ) -> ValidationReport:
        """Update a preliminary validation report with persisted artifact completeness."""
        artifacts_complete, missing_artifacts = StyleValidator.validate_artifact_completeness(output_dir)
        issues = list(report.issues)
        issues.extend(f"Missing artifact: {artifact}" for artifact in missing_artifacts)
        deduped_issues = list(dict.fromkeys(issues))
        return report.model_copy(
            update={
                "artifacts_complete": artifacts_complete,
                "missing_artifacts": missing_artifacts,
                "issues": deduped_issues,
            }
        )
    
    @staticmethod
    def create_output_directory(scene_name: str = "scene") -> Path:
        """
        Create a timestamped output directory.
        
        Args:
            scene_name: Name/slug for the scene
            
        Returns:
            Path to created output directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        scene_slug = slugify(scene_name)
        if not scene_slug:
            scene_slug = "untitled"
        
        dir_name = f"{timestamp}_{scene_slug}"
        output_path = Path(Config.APP_OUTPUT_DIR) / dir_name
        
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    @staticmethod
    def save_text_artifact(
        output_dir: Path,
        filename: str,
        content: str
    ) -> Path:
        """
        Save a text artifact.
        
        Args:
            output_dir: Output directory path
            filename: Filename
            content: Text content
            
        Returns:
            Path to saved file
        """
        file_path = output_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path
    
    @staticmethod
    def save_image_artifact(
        output_dir: Path,
        filename: str,
        image_data: bytes
    ) -> Path:
        """
        Save an image artifact.
        
        Args:
            output_dir: Output directory path
            filename: Filename
            image_data: Image bytes
            
        Returns:
            Path to saved file
        """
        file_path = output_dir / filename
        file_path.write_bytes(image_data)
        return file_path
    
    @staticmethod
    def save_image_from_path(
        output_dir: Path,
        filename: str,
        source_path: Path
    ) -> Path:
        """
        Copy image file from source to output directory.
        
        Args:
            output_dir: Output directory path
            filename: Target filename
            source_path: Source image path
            
        Returns:
            Path to saved file
        """
        image = Image.open(source_path)
        output_path = output_dir / filename
        image.save(output_path)
        return output_path
    
    @staticmethod
    def save_json_artifact(
        output_dir: Path,
        filename: str,
        data: Dict[str, Any]
    ) -> Path:
        """
        Save a JSON artifact.
        
        Args:
            output_dir: Output directory path
            filename: Filename
            data: Dictionary to save as JSON
            
        Returns:
            Path to saved file
        """
        file_path = output_dir / filename
        
        # Handle Pydantic models
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        
        file_path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8"
        )
        return file_path
    
    @staticmethod
    def save_generation_artifacts(
        output_dir: Path,
        final_image_bytes: bytes,
        final_prompt: str,
        negative_prompt: str,
        brief_dict: Dict[str, Any],
        metadata: GenerationMetadata,
        processed_sketch_path: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Save all required generation artifacts.
        
        Args:
            output_dir: Output directory
            final_image_bytes: Generated image bytes
            final_prompt: Final prompt used
            negative_prompt: Negative prompt used
            brief_dict: Structured brief as dict
            metadata: Generation metadata
            processed_sketch_path: Optional path to processed sketch
            
        Returns:
            Dictionary mapping artifact names to paths
        """
        artifacts = {}
        
        # Save final image
        artifacts["final.png"] = OutputManager.save_image_artifact(
            output_dir, "final.png", final_image_bytes
        )
        
        # Save prompts
        artifacts["prompt.txt"] = OutputManager.save_text_artifact(
            output_dir, "prompt.txt", final_prompt
        )
        
        artifacts["negative_prompt.txt"] = OutputManager.save_text_artifact(
            output_dir, "negative_prompt.txt", negative_prompt
        )
        
        # Save brief
        artifacts["brief.json"] = OutputManager.save_json_artifact(
            output_dir, "brief.json", brief_dict
        )
        
        # Save metadata
        artifacts["generation_response.json"] = OutputManager.save_json_artifact(
            output_dir, "generation_response.json", metadata.model_dump()
        )
        
        # Save processed sketch if provided
        if processed_sketch_path and processed_sketch_path.exists():
            target_path = output_dir / "processed_sketch.png"
            if processed_sketch_path.resolve() == target_path.resolve():
                artifacts["processed_sketch.png"] = processed_sketch_path
            else:
                artifacts["processed_sketch.png"] = OutputManager.save_image_from_path(
                    output_dir, "processed_sketch.png", processed_sketch_path
                )
        
        return artifacts
    
    @staticmethod
    def save_validation_report(
        output_dir: Path,
        report: ValidationReport
    ) -> Path:
        """
        Save a validation report.
        
        Args:
            output_dir: Output directory
            report: ValidationReport object
            
        Returns:
            Path to saved report
        """
        return OutputManager.save_json_artifact(
            output_dir, "validation_report.json", report.model_dump()
        )
    
    @staticmethod
    def get_latest_output_dir(scene_name: Optional[str] = None) -> Optional[Path]:
        """
        Get the most recently created output directory.
        
        Args:
            scene_name: Optional filter by scene name slug
            
        Returns:
            Path to latest directory or None
        """
        output_root = Path(Config.APP_OUTPUT_DIR)
        if not output_root.exists():
            return None
        
        # Get all timestamped directories
        dirs = []
        for item in output_root.iterdir():
            if item.is_dir() and "_" in item.name:
                dirs.append(item)
        
        if not dirs:
            return None
        
        # Sort by timestamp (directories are named YYYY-MM-DD_HHMM_scene)
        dirs.sort(key=lambda p: p.name, reverse=True)
        
        if scene_name:
            scene_slug = slugify(scene_name)
            for d in dirs:
                if scene_slug in d.name:
                    return d
            return None
        
        return dirs[0]
