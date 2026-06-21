"""Tests for orientation handling in the generate CLI."""

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
            "output_dir": Path("output/run-002"),
            "image_path": Path("output/run-002/final.png"),
            "prompt_path": Path("output/run-002/prompt.txt"),
            "negative_prompt_path": Path("output/run-002/negative_prompt.txt"),
            "brief_path": Path("output/run-002/brief.json"),
            "metadata_path": Path("output/run-002/generation_response.json"),
            "validation_path": Path("output/run-002/validation_report.json"),
        }


def test_generate_prompts_for_orientation_when_missing(monkeypatch):
    """Generate should prompt interactively when orientation is omitted."""
    service = StubGenerationService()
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: service)

    result = runner.invoke(
        app,
        ["generate", "--prompt", "Moonlit village square", "--mode", "draft"],
        input="square\n",
    )

    assert result.exit_code == 0
    assert service.calls[0]["orientation"] == Orientation.SQUARE
    assert "orientation" in result.stdout.lower()


def test_generate_rejects_missing_orientation_in_non_interactive_mode(monkeypatch):
    """Generate should fail visibly when orientation is missing in non-interactive mode."""
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: StubGenerationService())

    result = runner.invoke(
        app,
        ["generate", "--prompt", "Moonlit village square", "--mode", "draft"],
        input=None,
    )

    assert result.exit_code != 0
    assert "orientation" in result.stdout.lower()


def test_generate_rejects_invalid_orientation(monkeypatch):
    """Generate should reject unsupported orientation values."""
    monkeypatch.setattr("scenografia.main.TextGenerationService", lambda: StubGenerationService())

    result = runner.invoke(
        app,
        [
            "generate",
            "--prompt",
            "Moonlit village square",
            "--mode",
            "draft",
            "--orientation",
            "diagonal",
        ],
    )

    assert result.exit_code != 0
    assert "invalid value" in result.stdout.lower() or "orientation" in result.stdout.lower()