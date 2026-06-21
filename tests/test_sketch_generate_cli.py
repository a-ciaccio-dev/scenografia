"""Tests for sketch-mode generate CLI behavior."""

from pathlib import Path

from typer.testing import CliRunner

from scenografia.main import app
from scenografia.schemas.generation_schema import Orientation


runner = CliRunner()


class StubSketchService:
    def __init__(self):
        self.calls = []

    def run_sketch_generation(self, sketch_path, style, mode, orientation, model, disable_ai_refinement):
        self.calls.append(
            {
                "sketch_path": sketch_path,
                "style": style,
                "mode": mode,
                "orientation": orientation,
                "model": model,
                "disable_ai_refinement": disable_ai_refinement,
            }
        )
        return {
            "output_dir": Path("output/run-004"),
            "processed_sketch_path": Path("output/run-004/processed_sketch.png"),
            "image_path": Path("output/run-004/final.png"),
        }


def test_generate_sketch_persists_processed_sketch_and_style_guidance(monkeypatch):
    """Sketch generate should route sketch path and style guidance to the sketch service."""
    service = StubSketchService()
    monkeypatch.setattr("scenografia.main.SketchGenerationService", lambda: service)

    result = runner.invoke(
        app,
        [
            "generate",
            "--sketch",
            "tests/fixtures/sketch_dummy.png",
            "--style",
            "fairytale theatrical backdrop",
            "--mode",
            "vector-ready",
            "--orientation",
            "portrait",
        ],
    )

    assert result.exit_code == 0
    assert service.calls == [
        {
            "sketch_path": "tests/fixtures/sketch_dummy.png",
            "style": "fairytale theatrical backdrop",
            "mode": "vector-ready",
            "orientation": Orientation.PORTRAIT,
            "model": None,
            "disable_ai_refinement": False,
        }
    ]
    assert "processed_sketch.png" in result.stdout


def test_generate_sketch_requires_style_guidance(monkeypatch):
    """Sketch mode should fail visibly when style guidance is omitted."""
    monkeypatch.setattr("scenografia.main.SketchGenerationService", lambda: StubSketchService())

    result = runner.invoke(
        app,
        [
            "generate",
            "--sketch",
            "tests/fixtures/sketch_dummy.png",
            "--mode",
            "standard",
            "--orientation",
            "landscape",
        ],
    )

    assert result.exit_code != 0
    assert "style" in result.stdout.lower() or "style" in result.stderr.lower()