"""Tests for scenic style contract validation."""

import json
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from scenografia.agents.style_compliance_agent import StyleComplianceAgent
from scenografia.schemas.generation_schema import Orientation
from scenografia.tools.style_validator import StyleValidator


class TestScenicStyleValidation:
    """Test scenic style compliance validation."""
    
    def test_validates_theatrical_prompt(self):
        """Should validate theatrical style prompts."""
        prompt = "A dramatic theatrical backdrop with ancient stone pillars"
        negative = "No photorealism, no gradients, no blur"
        
        is_valid, issues = StyleValidator.validate_scenic_style(prompt, negative)
        assert is_valid, f"Prompt should be valid but got issues: {issues}"
    
    def test_rejects_missing_style_indicators(self):
        """Should reject prompts missing style indicators."""
        prompt = "A nice landscape"
        negative = "Avoid X"
        
        is_valid, issues = StyleValidator.validate_scenic_style(prompt, negative)
        assert not is_valid
        assert len(issues) > 0
    
    def test_rejects_photorealism(self):
        """Should reject photorealism in prompt."""
        prompt = "A photorealistic theatrical scene"
        negative = "Avoid X"
        
        is_valid, issues = StyleValidator.validate_scenic_style(prompt, negative)
        assert not is_valid
        assert any("photorealistic" in str(i).lower() for i in issues)
    
    def test_requires_negative_prompt(self):
        """Should validate presence of negative prompt."""
        prompt = "Theatrical scene"
        negative = ""  # Empty
        
        is_valid, issues = StyleValidator.validate_scenic_style(prompt, negative)
        assert not is_valid
        assert any("negative" in str(i).lower() for i in issues)


class TestArtifactCompleteness:
    """Test artifact completeness validation."""
    
    def test_detects_missing_artifacts(self):
        """Should detect missing artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create only one artifact
            (output_dir / "final.png").touch()
            
            is_complete, missing = StyleValidator.validate_artifact_completeness(output_dir)
            
            assert not is_complete
            assert len(missing) > 0
            assert "prompt.txt" in missing
    
    def test_accepts_complete_artifacts(self):
        """Should accept when all artifacts present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create all required artifacts
            for artifact in StyleValidator.REQUIRED_ARTIFACTS:
                (output_dir / artifact).touch()
            
            is_complete, missing = StyleValidator.validate_artifact_completeness(output_dir)
            
            assert is_complete
            assert len(missing) == 0


class TestOrientationPersistence:
    """Test orientation persistence in artifacts."""
    
    def test_validates_orientation_in_metadata(self):
        """Should validate orientation in metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create metadata with orientation
            metadata = {
                "orientation": "landscape",
                "run_id": "test-001"
            }
            metadata_path = output_dir / "generation_response.json"
            metadata_path.write_text(json.dumps(metadata))
            
            # Create validation report with orientation
            report = {
                "orientation": "landscape",
                "orientation_valid": True
            }
            report_path = output_dir / "validation_report.json"
            report_path.write_text(json.dumps(report))
            
            is_valid, issues = StyleValidator.validate_orientation_persistence(
                metadata_path, report_path
            )
            
            assert is_valid
            assert len(issues) == 0
    
    def test_detects_missing_orientation(self):
        """Should detect missing orientation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create metadata without orientation
            metadata = {"run_id": "test-001"}
            metadata_path = output_dir / "generation_response.json"
            metadata_path.write_text(json.dumps(metadata))
            
            report = {"test": "data"}
            report_path = output_dir / "validation_report.json"
            report_path.write_text(json.dumps(report))
            
            is_valid, issues = StyleValidator.validate_orientation_persistence(
                metadata_path, report_path
            )
            
            assert not is_valid
            assert any("orientation" in str(i).lower() for i in issues)


class TestImageQualityValidation:
    """Test image quality validation."""
    
    def test_detects_missing_image(self):
        """Should reject missing image."""
        image_path = Path("/nonexistent/image.png")
        is_valid, metrics = StyleValidator.validate_image_quality(image_path)
        
        assert not is_valid
        assert not metrics["exists"]
    
    def test_validates_real_image(self):
        """Should validate real image file."""
        from PIL import Image
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            img = Image.new("RGB", (640, 480), color="red")
            image_path = Path(tmpdir) / "test.png"
            img.save(image_path)
            
            is_valid, metrics = StyleValidator.validate_image_quality(image_path)
            
            assert is_valid
            assert metrics["exists"]
            assert metrics["has_color"]
            assert metrics["dimensions"] == (640, 480)
    
    def test_rejects_small_image(self):
        """Should reject very small images."""
        from PIL import Image
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tiny image
            img = Image.new("RGB", (10, 10), color="red")
            image_path = Path(tmpdir) / "tiny.png"
            img.save(image_path)
            
            is_valid, metrics = StyleValidator.validate_image_quality(image_path)
            
            # Should reject as too small
            assert not is_valid


class TestComprehensiveOutputValidation:
    """Test comprehensive output folder validation."""
    
    def test_validates_complete_output_folder(self):
        """Should validate complete output folder."""
        from PIL import Image
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create all artifacts
            # Image
            img = Image.new("RGB", (640, 480), color="blue")
            img.save(output_dir / "final.png")
            
            # Prompts
            (output_dir / "prompt.txt").write_text("Test prompt")
            (output_dir / "negative_prompt.txt").write_text("No blur")
            
            # JSON files
            (output_dir / "brief.json").write_text("{}")
            
            metadata = {"orientation": "landscape"}
            (output_dir / "generation_response.json").write_text(json.dumps(metadata))
            
            validation = {
                "orientation": "landscape",
                "orientation_valid": True
            }
            (output_dir / "validation_report.json").write_text(json.dumps(validation))
            
            report = StyleValidator.validate_output_folder(output_dir)
            
            assert report["exists"]
            assert report["artifacts_complete"]
            assert report["image_valid"]
            assert report["orientation_persistent"]
            assert len(report["issues"]) == 0
    
    def test_validation_report_structure(self):
        """Validation report should have expected structure."""
        report = StyleValidator.validate_output_folder(Path("/nonexistent"))
        
        assert "folder" in report
        assert "exists" in report
        assert "artifacts_complete" in report
        assert "issues" in report


class TestStyleComplianceAgent:
    """Test run-level validation report generation."""

    def test_validate_run_folder_records_required_status_fields(self):
        """Validation report should capture style, negative constraints, completeness, and issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            Image.new("RGB", (640, 480), color="blue").save(output_dir / "final.png")
            (output_dir / "prompt.txt").write_text(
                "Theatrical scenic design for a painted village backdrop with full color and clean outlines.",
                encoding="utf-8",
            )
            (output_dir / "negative_prompt.txt").write_text(
                "Avoid photorealism, 3D-render aesthetics, blurry edges, text, logos, or watermarks.",
                encoding="utf-8",
            )
            (output_dir / "brief.json").write_text("{}", encoding="utf-8")
            (output_dir / "generation_response.json").write_text(
                json.dumps({"run_id": "run-001", "orientation": "landscape"}),
                encoding="utf-8",
            )

            report = StyleComplianceAgent().validate_run_folder(output_dir)

            assert report.run_id == "run-001"
            assert report.orientation == Orientation.LANDSCAPE
            assert report.orientation_valid is True
            assert report.style_contract_applied is True
            assert report.negative_constraints_applied is True
            assert report.artifacts_complete is True
            assert report.issues == []

    def test_validate_run_folder_reports_missing_constraints_and_artifacts(self):
        """Validation report should collect issues for missing contract signals and artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            Image.new("RGB", (640, 480), color="blue").save(output_dir / "final.png")
            (output_dir / "prompt.txt").write_text("A generic landscape illustration.", encoding="utf-8")
            (output_dir / "negative_prompt.txt").write_text("Avoid blur.", encoding="utf-8")
            (output_dir / "generation_response.json").write_text(
                json.dumps({"run_id": "run-002", "orientation": "portrait"}),
                encoding="utf-8",
            )

            report = StyleComplianceAgent().validate_run_folder(output_dir)

            assert report.orientation == Orientation.PORTRAIT
            assert report.style_contract_applied is False
            assert report.negative_constraints_applied is False
            assert report.artifacts_complete is False
            assert any("brief.json" in issue for issue in report.issues)
            assert any("negative" in issue.lower() for issue in report.issues)


class TestValidationConstants:
    """Test validation constant definitions."""
    
    def test_required_artifacts_defined(self):
        """Should have required artifacts list."""
        assert len(StyleValidator.REQUIRED_ARTIFACTS) > 0
        assert "final.png" in StyleValidator.REQUIRED_ARTIFACTS
        assert "prompt.txt" in StyleValidator.REQUIRED_ARTIFACTS
    
    def test_scenic_requirements_defined(self):
        """Should have scenic requirements."""
        assert len(StyleValidator.SCENIC_REQUIREMENTS) > 0
    
    def test_prohibitions_defined(self):
        """Should have style prohibitions."""
        assert len(StyleValidator.STYLE_PROHIBITIONS) > 0
        assert "photorealism" in StyleValidator.STYLE_PROHIBITIONS
