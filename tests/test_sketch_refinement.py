"""Tests for optional sketch refinement handling."""

from pathlib import Path

from typer.testing import CliRunner

from scenografia.main import app
from scenografia.schemas.generation_schema import GenerationMode, GenerationRequest, Orientation


runner = CliRunner()


def test_sketch_generation_service_disables_ai_refinement_when_requested(monkeypatch):
    """Sketch service should pass the disable flag through to the interpreter."""
    from scenografia.agents.image_generation_agent import SketchGenerationService

    captured = {}

    class StubInterpreter:
        def interpret(self, request: GenerationRequest, output_dir: Path):
            captured["request"] = request
            return type(
                "Interpretation",
                (),
                {
                    "processed_sketch_path": str(output_dir / "processed_sketch.png"),
                    "scene_elements": ["tree line"],
                    "composition_notes": "center focus",
                    "refinement_applied": request.refine_sketch,
                    "refinement_description": None,
                    "preprocessing_details": {"steps": ["local"]},
                },
            )()

    service = SketchGenerationService(sketch_interpreter=StubInterpreter())
    monkeypatch.setattr(
        "scenografia.agents.image_generation_agent.SketchGenerationService._complete_generation",
        lambda self, request, brief, prompt_package, interpretation: {
            "output_dir": "output/run-005",
            "processed_sketch_path": interpretation.processed_sketch_path,
        },
    )

    result = service.run_sketch_generation(
        sketch_path="tests/fixtures/sketch_dummy.png",
        style="storybook",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        model=None,
        disable_ai_refinement=True,
    )

    assert result["processed_sketch_path"].endswith("processed_sketch.png")
    assert captured["request"].refine_sketch is False


def test_generate_sketch_cli_exposes_disable_ai_refinement_flag(monkeypatch):
    """CLI should forward the disable-ai-refinement option to sketch generation."""
    calls = []

    class StubSketchService:
        def run_sketch_generation(self, sketch_path, style, mode, orientation, model, disable_ai_refinement):
            calls.append(disable_ai_refinement)
            return {
                "output_dir": Path("output/run-006"),
                "processed_sketch_path": Path("output/run-006/processed_sketch.png"),
                "image_path": Path("output/run-006/final.png"),
            }

    monkeypatch.setattr("scenografia.main.SketchGenerationService", lambda: StubSketchService())

    result = runner.invoke(
        app,
        [
            "generate",
            "--sketch",
            "tests/fixtures/sketch_dummy.png",
            "--style",
            "storybook backdrop",
            "--mode",
            "draft",
            "--orientation",
            "square",
            "--disable-ai-refinement",
        ],
    )

    assert result.exit_code == 0
    assert calls == [True]