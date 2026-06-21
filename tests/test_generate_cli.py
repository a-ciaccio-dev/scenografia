"""Tests for text-mode generate CLI happy path."""

from pathlib import Path

from typer.testing import CliRunner

from scenografia.main import app
from scenografia.schemas.generation_schema import Orientation


runner = CliRunner()


class StubGenerationService:
    """Stub service used to isolate CLI behavior."""

    def __init__(self):
        self.calls = []

    def run_text_generation(self, prompt: str, mode: str, orientation: Orientation, model: str | None):
        self.calls.append(
            {
                "prompt": prompt,
                "mode": mode,
                "orientation": orientation,
                "model": model,
            }
        )
        return {
            "output_dir": Path("output/run-001"),
            "image_path": Path("output/run-001/final.png"),
            "prompt_path": Path("output/run-001/prompt.txt"),
            "negative_prompt_path": Path("output/run-001/negative_prompt.txt"),
            "brief_path": Path("output/run-001/brief.json"),
            "metadata_path": Path("output/run-001/generation_response.json"),
            "validation_path": Path("output/run-001/validation_report.json"),
        }


def test_generate_text_happy_path(monkeypatch):
    """Generate should accept a text prompt and report the output directory."""
    service = StubGenerationService()
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: service)

    result = runner.invoke(
        app,
        [
            "generate",
            "--prompt",
            "Sunlit enchanted forest clearing",
            "--mode",
            "standard",
            "--orientation",
            "landscape",
        ],
    )

    assert result.exit_code == 0
    assert service.calls == [
        {
            "prompt": "Sunlit enchanted forest clearing",
            "mode": "standard",
            "orientation": Orientation.LANDSCAPE,
            "model": None,
        }
    ]
    assert "output/run-001" in result.stdout


def test_generate_text_allows_model_override(monkeypatch):
    """Generate should pass an explicit model override to the service."""
    service = StubGenerationService()
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: service)

    result = runner.invoke(
        app,
        [
            "generate",
            "--prompt",
            "Castle courtyard backdrop",
            "--mode",
            "production",
            "--orientation",
            "portrait",
            "--model",
            "custom/model",
        ],
    )

    assert result.exit_code == 0
    assert service.calls[0]["model"] == "custom/model"
    assert service.calls[0]["orientation"] == Orientation.PORTRAIT