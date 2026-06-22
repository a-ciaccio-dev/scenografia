"""Tests for web_helpers and web_app."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from scenografia.web_helpers import (
    sanitize_filename,
    list_recent_runs,
    read_validation_report,
    find_final_image,
    find_processed_sketch,
    read_prompt_file,
    save_uploaded_sketch,
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""
    
    def test_extracts_filename_from_path(self):
        """Should extract only the filename from path."""
        result = sanitize_filename("../../evil/file.png")
        assert result == "file.png"
        assert ".." not in result
        assert "/" not in result
    
    def test_removes_path_traversal(self):
        """Should remove ../ patterns."""
        result = sanitize_filename("../../etc/passwd.png")
        assert ".." not in result
        assert result == "passwd.png"
    
    def test_preserves_alphanumeric_and_dots(self):
        """Should keep alphanumeric, dash, underscore, dot."""
        result = sanitize_filename("my-file_v2.png")
        assert result == "my-file_v2.png"
    
    def test_replaces_invalid_chars(self):
        """Should replace invalid characters with _."""
        result = sanitize_filename("my@file#2024.png")
        assert "@" not in result and "#" not in result
        assert "my_file_2024.png" == result
    
    def test_handles_empty_input(self):
        """Should return safe default for empty input."""
        result = sanitize_filename("")
        assert result == "upload"
        assert len(result) > 0
    
    def test_truncates_long_filenames(self):
        """Should truncate filenames exceeding max_length."""
        long_name = "a" * 300 + ".png"
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100
    
    def test_handles_complex_paths(self):
        """Should handle complex path structures."""
        result = sanitize_filename("C:\\Users\\evil\\downloads\\my-sketch.png")
        assert result == "my-sketch.png"
        assert "\\" not in result
        assert ":" not in result


class TestListRecentRuns:
    """Tests for listing recent generation runs."""
    
    def test_returns_empty_list_if_dir_not_exists(self):
        """Should return [] if output dir doesn't exist."""
        result = list_recent_runs("/nonexistent/path", n=5)
        assert result == []
    
    def test_returns_empty_list_if_no_runs(self, tmp_path):
        """Should return [] if dir has no run subdirectories."""
        result = list_recent_runs(tmp_path, n=5)
        assert result == []
    
    def test_sorts_runs_by_name_descending(self, tmp_path):
        """Should sort runs newest-first (descending)."""
        # Create fake run directories
        (tmp_path / "2026-06-20_1000_run-001").mkdir()
        (tmp_path / "2026-06-22_1200_run-003").mkdir()
        (tmp_path / "2026-06-21_1100_run-002").mkdir()
        
        result = list_recent_runs(tmp_path, n=10)
        
        assert len(result) == 3
        # Most recent first
        assert result[0].name == "2026-06-22_1200_run-003"
        assert result[1].name == "2026-06-21_1100_run-002"
        assert result[2].name == "2026-06-20_1000_run-001"
    
    def test_respects_n_limit(self, tmp_path):
        """Should return at most n runs."""
        for i in range(15):
            (tmp_path / f"2026-06-22_120{i%10:d}_run-{i:03d}").mkdir()
        
        result = list_recent_runs(tmp_path, n=5)
        assert len(result) == 5
    
    def test_ignores_non_run_directories(self, tmp_path):
        """Should ignore directories not matching run pattern."""
        (tmp_path / "2026-06-22_1200_run-001").mkdir()
        (tmp_path / "random_folder").mkdir()
        (tmp_path / "input").mkdir()
        
        result = list_recent_runs(tmp_path, n=10)
        assert len(result) == 1
        assert result[0].name == "2026-06-22_1200_run-001"


class TestReadValidationReport:
    """Tests for reading validation_report.json."""
    
    def test_returns_none_if_file_not_exists(self, tmp_path):
        """Should return None if validation_report.json doesn't exist."""
        result = read_validation_report(tmp_path)
        assert result is None
    
    def test_returns_dict_from_valid_json(self, tmp_path):
        """Should parse and return JSON dict."""
        report = {"orientation_valid": True, "style_compliant": True}
        report_path = tmp_path / "validation_report.json"
        report_path.write_text(json.dumps(report))
        
        result = read_validation_report(tmp_path)
        assert result == report
    
    def test_returns_none_if_json_invalid(self, tmp_path):
        """Should return None on JSON decode error."""
        report_path = tmp_path / "validation_report.json"
        report_path.write_text("{ invalid json")
        
        result = read_validation_report(tmp_path)
        assert result is None


class TestFindFinalImage:
    """Tests for finding final.png."""
    
    def test_returns_none_if_not_exists(self, tmp_path):
        """Should return None if final.png doesn't exist."""
        result = find_final_image(tmp_path)
        assert result is None
    
    def test_returns_path_if_exists(self, tmp_path):
        """Should return Path if final.png exists."""
        final_path = tmp_path / "final.png"
        final_path.write_bytes(b"fake-image")
        
        result = find_final_image(tmp_path)
        assert result == final_path


class TestFindProcessedSketch:
    """Tests for finding processed_sketch.png."""
    
    def test_returns_none_if_not_exists(self, tmp_path):
        """Should return None if processed_sketch.png doesn't exist."""
        result = find_processed_sketch(tmp_path)
        assert result is None
    
    def test_returns_path_if_exists(self, tmp_path):
        """Should return Path if processed_sketch.png exists."""
        sketch_path = tmp_path / "processed_sketch.png"
        sketch_path.write_bytes(b"fake-sketch")
        
        result = find_processed_sketch(tmp_path)
        assert result == sketch_path


class TestReadPromptFile:
    """Tests for reading prompt.txt."""
    
    def test_returns_none_if_not_exists(self, tmp_path):
        """Should return None if prompt.txt doesn't exist."""
        result = read_prompt_file(tmp_path)
        assert result is None
    
    def test_returns_content_from_directory(self, tmp_path):
        """Should read prompt.txt from directory."""
        prompt_path = tmp_path / "prompt.txt"
        prompt_path.write_text("A mystical forest with ancient pillars")
        
        result = read_prompt_file(tmp_path)
        assert result == "A mystical forest with ancient pillars"
    
    def test_returns_content_from_file_directly(self, tmp_path):
        """Should read from file if given direct file path."""
        prompt_path = tmp_path / "prompt.txt"
        prompt_path.write_text("Direct file read")
        
        result = read_prompt_file(prompt_path)
        assert result == "Direct file read"
    
    def test_handles_both_directory_and_file_paths(self, tmp_path):
        """Should work with both directory and file paths."""
        prompt_path = tmp_path / "prompt.txt"
        prompt_path.write_text("Test content")
        
        # Test with directory
        result_dir = read_prompt_file(tmp_path)
        # Test with file
        result_file = read_prompt_file(prompt_path)
        
        assert result_dir == result_file == "Test content"


class TestSaveUploadedSketch:
    """Tests for saving uploaded sketch files."""
    
    def test_saves_file_to_sketches_dir(self, tmp_path):
        """Should save bytes to sketches directory with safe filename."""
        sketches_dir = tmp_path / "input/sketches"
        file_bytes = b"fake-image-data"
        filename = "my-sketch.png"
        
        result = save_uploaded_sketch(file_bytes, filename, sketches_dir)
        
        assert result.exists()
        assert result.read_bytes() == file_bytes
        assert result.parent == sketches_dir
    
    def test_creates_sketches_dir_if_missing(self, tmp_path):
        """Should create sketches directory if it doesn't exist."""
        sketches_dir = tmp_path / "input/sketches"
        assert not sketches_dir.exists()
        
        save_uploaded_sketch(b"test", "test.png", sketches_dir)
        
        assert sketches_dir.exists()
    
    def test_sanitizes_filename(self, tmp_path):
        """Should sanitize filename for safe storage."""
        sketches_dir = tmp_path / "input/sketches"
        
        result = save_uploaded_sketch(
            b"test", 
            "../../evil/file.png",
            sketches_dir
        )
        
        # Should not contain path traversal
        assert ".." not in result.name
        assert "/" not in result.name
        assert result.parent == sketches_dir
        assert result.name == "file.png"


class TestWebAppImport:
    """Tests for web_app module import without heavy dependencies."""
    
    def test_load_config_imported_independently(self):
        """Should be able to import load_config without Streamlit."""
        from scenografia.web_app import load_config
        assert callable(load_config)
    
    def test_wrapper_functions_imported_independently(self):
        """Should be able to import wrapper functions without Streamlit."""
        from scenografia.web_app import run_text_generation, run_sketch_generation
        assert callable(run_text_generation)
        assert callable(run_sketch_generation)


class TestLoadConfigSafety:
    """Tests for load_config error handling."""
    
    @patch("scenografia.config.Config")
    def test_load_config_success(self, mock_config):
        """Should return (True, '') on success."""
        mock_config.initialize.return_value = None
        
        from scenografia.web_app import load_config
        
        success, msg = load_config()
        assert success is True
        assert msg == ""
    
    @patch("scenografia.config.Config")
    def test_load_config_missing_api_key(self, mock_config):
        """Should return (False, message) on KeyError without exposing key."""
        mock_config.initialize.side_effect = KeyError("OPENROUTER_API_KEY")
        
        from scenografia.web_app import load_config
        
        success, msg = load_config()
        assert success is False
        assert "OPENROUTER_API_KEY" in msg
        assert "your-key" not in msg
    
    @patch("scenografia.config.Config")
    def test_load_config_value_error(self, mock_config):
        """Should handle ValueError gracefully."""
        mock_config.initialize.side_effect = ValueError("Bad config")
        
        from scenografia.web_app import load_config
        
        success, msg = load_config()
        assert success is False
        assert len(msg) > 0


class TestWrapperFunctions:
    """Tests for service wrapper functions."""
    
    @patch("scenografia.agents.image_generation_agent.TextGenerationService")
    def test_run_text_generation_calls_service(self, mock_service_class):
        """Should call TextGenerationService with correct args."""
        mock_service = MagicMock()
        mock_service.run_text_generation.return_value = {
            "output_dir": Path("output/run-001"),
            "image_path": Path("output/run-001/final.png"),
        }
        mock_service_class.return_value = mock_service
        
        from scenografia.web_app import run_text_generation
        
        result = run_text_generation(
            prompt="Test prompt",
            mode="standard",
            orientation="landscape"
        )
        
        mock_service.run_text_generation.assert_called_once()
        call_kwargs = mock_service.run_text_generation.call_args.kwargs
        assert call_kwargs["prompt"] == "Test prompt"
        assert result["output_dir"] == Path("output/run-001")
    
    @patch("scenografia.agents.image_generation_agent.SketchGenerationService")
    def test_run_sketch_generation_calls_service(self, mock_service_class):
        """Should call SketchGenerationService with correct args."""
        mock_service = MagicMock()
        mock_service.run_sketch_generation.return_value = {
            "output_dir": Path("output/run-002"),
            "processed_sketch_path": Path("output/run-002/processed_sketch.png"),
        }
        mock_service_class.return_value = mock_service
        
        from scenografia.web_app import run_sketch_generation
        
        result = run_sketch_generation(
            sketch_path="input/sketches/test.png",
            style="theatrical",
            mode="standard",
            orientation="portrait"
        )
        
        mock_service.run_sketch_generation.assert_called_once()
        call_kwargs = mock_service.run_sketch_generation.call_args.kwargs
        assert call_kwargs["sketch_path"] == "input/sketches/test.png"
