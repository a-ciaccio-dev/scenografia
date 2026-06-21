"""Tests for output artifact persistence and directory management."""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from scenografia.tools.output_manager import (
    OutputManager,
    slugify
)
from scenografia.schemas.validation_schema import (
    GenerationMetadata,
    ValidationReport
)
from scenografia.schemas.generation_schema import Orientation


class TestSlugify:
    """Test text slugification."""
    
    def test_slugify_spaces_to_hyphens(self):
        """Spaces should become hyphens."""
        assert slugify("my scene") == "my-scene"
    
    def test_slugify_lowercase(self):
        """Should convert to lowercase."""
        assert slugify("My Scene") == "my-scene"
    
    def test_slugify_removes_special_chars(self):
        """Should remove special characters."""
        assert slugify("My!Scene@#$") == "myscene"
    
    def test_slugify_multiple_spaces(self):
        """Multiple spaces become single hyphen."""
        assert slugify("my   scene") == "my-scene"
    
    def test_slugify_length_limit(self):
        """Slug should be length-limited."""
        long_text = "a" * 100
        result = slugify(long_text)
        assert len(result) <= 50


class TestOutputDirectoryCreation:
    """Test timestamped output directory creation."""
    
    def test_create_output_directory_creates_path(self):
        """Should create output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_output = Path("output")
            try:
                from scenografia.config import Config
                Config.APP_OUTPUT_DIR = tmpdir
                
                output_dir = OutputManager.create_output_directory("test-scene")
                assert output_dir.exists()
                assert output_dir.parent == Path(tmpdir)
            finally:
                Config.APP_OUTPUT_DIR = str(original_output)
    
    def test_output_directory_has_timestamp(self):
        """Output directory name should contain timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from scenografia.config import Config
            original = Config.APP_OUTPUT_DIR
            try:
                Config.APP_OUTPUT_DIR = tmpdir
                output_dir = OutputManager.create_output_directory("test")
                name = output_dir.name
                # Should contain YYYY-MM-DD_HHMM format
                assert "_" in name
                assert len(name.split("_")[0]) == 10  # YYYY-MM-DD
            finally:
                Config.APP_OUTPUT_DIR = original
    
    def test_output_directory_has_scene_name(self):
        """Output directory name should include scene name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from scenografia.config import Config
            original = Config.APP_OUTPUT_DIR
            try:
                Config.APP_OUTPUT_DIR = tmpdir
                output_dir = OutputManager.create_output_directory("forest-scene")
                name = output_dir.name
                assert "forest" in name
                assert "scene" in name
            finally:
                Config.APP_OUTPUT_DIR = original


class TestTextArtifactSaving:
    """Test saving text artifacts."""
    
    def test_save_text_artifact(self):
        """Should save text artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            content = "Test prompt content"
            
            result = OutputManager.save_text_artifact(
                output_dir, "test.txt", content
            )
            
            assert result.exists()
            assert result.read_text() == content
    
    def test_save_text_artifact_path_returned(self):
        """Should return path to saved file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            result = OutputManager.save_text_artifact(
                output_dir, "test.txt", "content"
            )
            
            assert isinstance(result, Path)
            assert "test.txt" in str(result)


class TestImageArtifactSaving:
    """Test saving image artifacts."""
    
    def test_save_image_artifact(self):
        """Should save image artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create simple image bytes (minimal PNG)
            image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            
            result = OutputManager.save_image_artifact(
                output_dir, "test.png", image_bytes
            )
            
            assert result.exists()
            assert result.stat().st_size > 0


class TestJSONArtifactSaving:
    """Test saving JSON artifacts."""
    
    def test_save_json_artifact_dict(self):
        """Should save dict as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            data = {"key": "value", "number": 42}
            
            result = OutputManager.save_json_artifact(
                output_dir, "test.json", data
            )
            
            assert result.exists()
            saved_data = json.loads(result.read_text())
            assert saved_data == data
    
    def test_save_json_artifact_pydantic_model(self):
        """Should save Pydantic model as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            metadata = GenerationMetadata(
                run_id="test-001",
                input_type="text",
                original_prompt="Test prompt",
                orientation=Orientation.LANDSCAPE,
                generation_mode="standard",
                model_id="test-model",
                final_prompt="Final prompt",
                negative_prompt="Negative"
            )
            
            result = OutputManager.save_json_artifact(
                output_dir, "metadata.json", metadata
            )
            
            assert result.exists()
            saved_data = json.loads(result.read_text())
            assert saved_data["run_id"] == "test-001"


class TestGenerationArtifactsSaving:
    """Test saving complete generation artifacts."""
    
    def test_save_all_artifacts_creates_files(self):
        """Should create all required artifact files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            metadata = GenerationMetadata(
                run_id="test-001",
                input_type="text",
                original_prompt="Test",
                orientation=Orientation.LANDSCAPE,
                generation_mode="standard",
                model_id="test-model",
                final_prompt="Final",
                negative_prompt="Negative"
            )
            
            artifacts = OutputManager.save_generation_artifacts(
                output_dir,
                final_image_bytes=b"fake-image-data",
                final_prompt="Test prompt",
                negative_prompt="Avoid X",
                brief_dict={"test": "data"},
                metadata=metadata
            )
            
            assert "final.png" in artifacts
            assert "prompt.txt" in artifacts
            assert "negative_prompt.txt" in artifacts
            assert "brief.json" in artifacts
            assert "generation_response.json" in artifacts


class TestValidationReportSaving:
    """Test saving validation reports."""
    
    def test_save_validation_report(self):
        """Should save validation report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            report = ValidationReport(
                report_id="val-001",
                run_id="gen-001",
                orientation=Orientation.LANDSCAPE,
                style_compliant=True,
                artifacts_complete=True
            )
            
            result = OutputManager.save_validation_report(
                output_dir, report
            )
            
            assert result.exists()
            saved = json.loads(result.read_text())
            assert saved["report_id"] == "val-001"


class TestLatestOutputDirectory:
    """Test finding latest output directory."""
    
    def test_get_latest_output_dir(self):
        """Should find most recent output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from scenografia.config import Config
            original = Config.APP_OUTPUT_DIR
            try:
                Config.APP_OUTPUT_DIR = tmpdir
                
                # Create a directory
                first_dir = OutputManager.create_output_directory("scene1")
                latest = OutputManager.get_latest_output_dir()
                
                assert latest is not None
                assert latest.exists()
            finally:
                Config.APP_OUTPUT_DIR = original
