"""Tests for fail-fast error handling in TextGenerationService and SketchGenerationService."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from PIL import Image

from scenografia.services.text_generation_service import TextGenerationService
from scenografia.services.sketch_generation_service import SketchGenerationService
from scenografia.schemas.generation_schema import GenerationMode, Orientation
from scenografia.schemas.sketch_schema import SketchInterpretation


def test_text_generation_service_failfast_on_unauthorized():
    """Verify that TextGenerationService stops immediately on 401/unauthorized error without 3 attempts."""
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = RuntimeError("API error: 401 Unauthorized")

    service = TextGenerationService(image_generator=mock_generator)

    with pytest.raises(RuntimeError) as exc_info:
        service.run_text_generation(
            prompt="A majestic palace ballroom",
            mode=GenerationMode.STANDARD,
            orientation=Orientation.LANDSCAPE,
            model=None,
        )

    assert "401" in str(exc_info.value)
    # Crucial assertion: generator was called EXACTLY ONCE (no useless retries)
    assert mock_generator.generate.call_count == 1


def test_text_generation_service_failfast_on_payment_required():
    """Verify that TextGenerationService stops immediately on 402/payment required without retries."""
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = RuntimeError("API error: 402 Payment Required: insufficient credits")

    service = TextGenerationService(image_generator=mock_generator)

    with pytest.raises(RuntimeError) as exc_info:
        service.run_text_generation(
            prompt="A majestic palace ballroom",
            mode=GenerationMode.STANDARD,
            orientation=Orientation.LANDSCAPE,
            model=None,
        )

    assert "402" in str(exc_info.value)
    assert mock_generator.generate.call_count == 1


def test_sketch_generation_service_failfast_on_unauthorized(tmp_path):
    """Verify that SketchGenerationService stops immediately on 401 without retries."""
    sketch_path = tmp_path / "sketch.png"
    Image.new("RGB", (100, 100), color=(255, 255, 255)).save(sketch_path)

    mock_generator = MagicMock()
    mock_generator.generate.side_effect = RuntimeError("API error: 401 Unauthorized")

    mock_interpreter = MagicMock()
    mock_interpreter.interpret.return_value = SketchInterpretation(
        processed_sketch_path=str(sketch_path),
        composition_description="Stage arch",
        detected_elements=["arch"],
        suggested_prompt="Theatrical scenic design sketch of arch",
    )

    service = SketchGenerationService(
        image_generator=mock_generator,
        sketch_interpreter=mock_interpreter,
    )

    with pytest.raises(RuntimeError) as exc_info:
        service.run_sketch_generation(
            sketch_path=str(sketch_path),
            style="Renaissance",
            mode=GenerationMode.STANDARD,
            orientation=Orientation.LANDSCAPE,
            model=None,
            disable_ai_refinement=True,
        )

    assert "401" in str(exc_info.value)
    assert mock_generator.generate.call_count == 1
