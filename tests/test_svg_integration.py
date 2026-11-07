"""
Integration tests for SVG vectorization in OutputManager, Service Layer, and CLI.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest
from typer.testing import CliRunner

from scenografia.main import app
from scenografia.schemas.brief_schema import StructuredBrief
from scenografia.schemas.generation_schema import GenerationMode, Orientation
from scenografia.schemas.validation_schema import GenerationMetadata, ValidationReport
from scenografia.tools.output_manager import OutputManager


@pytest.fixture
def dummy_png_bytes() -> bytes:
    """Create a minimal PNG byte sequence."""
    import io

    img = Image.new("RGB", (100, 100), color=(50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_output_manager_save_svg(tmp_path, dummy_png_bytes):
    """Test OutputManager.save_svg generates an SVG file."""
    img_path = tmp_path / "final.png"
    img_path.write_bytes(dummy_png_bytes)

    svg_path = OutputManager.save_svg(tmp_path, img_path)
    assert svg_path.exists()
    assert svg_path.name == "scene_vector.svg"
    assert "<svg" in svg_path.read_text(encoding="utf-8")


def test_output_manager_persist_text_run_with_svg(tmp_path, dummy_png_bytes):
    """Test persist_text_run generates SVG when export_svg=True."""
    brief = StructuredBrief(
        scene_description="Gothic Cathedral",
        style_requirements="Dark stone",
        orientation="landscape",
    )
    prompt_pkg = {"final_prompt": "A gothic cathedral", "negative_prompt": "text, watermark"}
    mock_resp = MagicMock()
    mock_resp.image_data = dummy_png_bytes
    mock_resp.request_id = "req_svg_123"
    mock_resp.model_used = "mock-model"
    mock_resp.image_url = None

    report = ValidationReport(
        report_id="val-123",
        run_id="req_svg_123",
        orientation="landscape",
        style_compliant=True,
        artifacts_complete=True,
        issues=[],
    )
    metadata = GenerationMetadata(
        run_id="req_svg_123",
        input_type="text",
        original_prompt="A gothic cathedral",
        orientation="landscape",
        generation_mode="standard",
        model_id="mock-model",
        brief=brief.model_dump(),
        final_prompt="A gothic cathedral",
        negative_prompt="text, watermark",
    )

    results = OutputManager.persist_text_run(
        brief=brief.model_dump(),
        prompt_package=prompt_pkg,
        response=mock_resp,
        validation_report=report,
        metadata=metadata,
        output_dir=tmp_path,
        export_svg=True,
    )

    assert "svg_path" in results
    assert results["svg_path"].exists()
    assert results["svg_path"].name == "scene_vector.svg"


def test_cli_generate_text_export_svg_flag(tmp_path, dummy_png_bytes):
    """Test CLI generate command with --export-svg option."""
    runner = CliRunner()
    fake_run_dir = tmp_path / "2026-06-25_1200_run-test"
    fake_run_dir.mkdir()
    fake_svg = fake_run_dir / "scene_vector.svg"
    fake_svg.write_text("<svg></svg>", encoding="utf-8")

    mock_result = {
        "output_dir": fake_run_dir,
        "image_path": fake_run_dir / "final.png",
        "prompt_path": fake_run_dir / "prompt.txt",
        "svg_path": fake_svg,
    }

    with patch("scenografia.services.text_generation_service.TextGenerationService.run_text_generation", return_value=mock_result) as mock_gen:
        result = runner.invoke(app, [
            "generate",
            "--prompt", "Ancient theater ruins",
            "--mode", "standard",
            "--orientation", "landscape",
            "--export-svg",
        ])

        assert result.exit_code == 0
        assert "Vector SVG saved to" in result.stdout
        assert mock_gen.call_args.kwargs.get("export_svg") is True
