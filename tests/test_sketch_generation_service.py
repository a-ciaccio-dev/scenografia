"""Unit and integration tests for SketchGenerationService."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from PIL import Image

from scenografia.services.sketch_generation_service import SketchGenerationService
from scenografia.schemas.generation_schema import GenerationMode, Orientation, ImageGenerationResponse
from scenografia.schemas.sketch_schema import SketchInterpretation


@pytest.fixture
def dummy_sketch(tmp_path):
    sketch_path = tmp_path / "test_sketch.png"
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    img.save(sketch_path)
    return sketch_path


def test_sketch_generation_service_export_svg_passes_without_name_error(tmp_path, dummy_sketch, monkeypatch):
    """Verify that export_svg parameter is properly propagated and does not raise NameError."""
    # Stub OutputManager root dir to tmp_path
    monkeypatch.setattr("scenografia.config.Config.APP_OUTPUT_DIR", str(tmp_path))

    # Mock generator returning valid image bytes
    mock_generator = MagicMock()
    img = Image.new("RGB", (100, 60), color=(100, 150, 200))
    img_bytes_io = Path(tmp_path / "raw.png")
    img.save(img_bytes_io)
    img_bytes = img_bytes_io.read_bytes()

    mock_generator.generate.return_value = ImageGenerationResponse(
        image_data=img_bytes,
        image_url="http://example.com/final.png",
        model_used="google/gemini-2.5-flash-image",
        request_id="test-run-123",
    )

    # Mock sketch interpreter to avoid full OpenCV analysis
    mock_interpreter = MagicMock()
    mock_interpreter.interpret.return_value = SketchInterpretation(
        processed_sketch_path=str(dummy_sketch),
        composition_description="Theatrical stage with arched portal",
        detected_elements=["portal", "stage"],
        suggested_prompt="Theatrical scenic design sketch of stage portal",
    )

    service = SketchGenerationService(
        image_generator=mock_generator,
        sketch_interpreter=mock_interpreter,
    )

    # Test with export_svg=True
    result_svg = service.run_sketch_generation(
        sketch_path=str(dummy_sketch),
        style="Baroque",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        model="google/gemini-2.5-flash-image",
        disable_ai_refinement=False,
        export_svg=True,
    )

    assert result_svg is not None
    assert "output_dir" in result_svg
    assert "image_path" in result_svg
    assert "scene_vector.svg" in [p.name for p in result_svg.get("output_dir").iterdir()]
    assert "svg_path" in result_svg

    # Test with export_svg=False
    result_no_svg = service.run_sketch_generation(
        sketch_path=str(dummy_sketch),
        style="Baroque",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        model="google/gemini-2.5-flash-image",
        disable_ai_refinement=False,
        export_svg=False,
    )

    assert result_no_svg is not None
    assert "output_dir" in result_no_svg
    assert "image_path" in result_no_svg
    assert "svg_path" not in result_no_svg
