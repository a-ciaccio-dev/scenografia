"""Tests for sketch interpretation orchestration."""

from pathlib import Path

import numpy as np

from scenografia.schemas.generation_schema import GenerationMode, GenerationRequest, Orientation


def test_sketch_interpreter_runs_local_preprocessing_before_any_refinement(tmp_path, monkeypatch):
    """Sketch interpreter should always preprocess locally before optional refinement."""
    from scenografia.agents.sketch_interpreter_agent import SketchInterpreterAgent

    call_order = []
    sketch_path = Path("tests/fixtures/sketch_dummy.png")
    processed_image = np.zeros((32, 32), dtype=np.uint8)

    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.preprocess_sketch",
        lambda path: call_order.append("preprocess") or processed_image,
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.load_sketch",
        lambda path: np.zeros((32, 32, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.save_processed_sketch",
        lambda image, output_path: call_order.append("save") or output_path.write_bytes(b"png") or True,
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.extract_sketch_elements",
        lambda image: {"total_contours": 3, "detected": [{"size": 10.0}]},
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.get_preprocessing_details",
        lambda original, processed: {"steps": ["local-preprocess"]},
    )

    def fake_refine(*args, **kwargs):
        call_order.append("refine")
        return "AI refinement summary"

    agent = SketchInterpreterAgent(refinement_callback=fake_refine)
    request = GenerationRequest(
        input_type="sketch",
        sketch_path=str(sketch_path),
        style_guidance="storybook backdrop",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        refine_sketch=True,
    )

    result = agent.interpret(request, tmp_path)

    assert call_order == ["preprocess", "save", "refine"]
    assert result.refinement_applied is True
    assert result.refinement_description == "AI refinement summary"
    assert Path(result.processed_sketch_path).exists()


def test_sketch_interpreter_returns_detected_scene_elements_without_refinement(tmp_path, monkeypatch):
    """Sketch interpreter should produce a local interpretation when refinement is disabled."""
    from scenografia.agents.sketch_interpreter_agent import SketchInterpreterAgent

    sketch_path = Path("tests/fixtures/sketch_dummy.png")
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.preprocess_sketch",
        lambda path: np.zeros((24, 24), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.load_sketch",
        lambda path: np.zeros((24, 24, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.save_processed_sketch",
        lambda image, output_path: output_path.write_bytes(b"png") or True,
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.extract_sketch_elements",
        lambda image: {
            "total_contours": 2,
            "detected": [
                {"size": 120.0, "perimeter": 40.0},
                {"size": 80.0, "perimeter": 28.0},
            ],
        },
    )
    monkeypatch.setattr(
        "scenografia.agents.sketch_interpreter_agent.SketchPreprocessor.get_preprocessing_details",
        lambda original, processed: {"steps": ["local-preprocess"]},
    )

    agent = SketchInterpreterAgent()
    request = GenerationRequest(
        input_type="sketch",
        sketch_path=str(sketch_path),
        style_guidance="storybook backdrop",
        mode=GenerationMode.VECTOR_READY,
        orientation=Orientation.PORTRAIT,
        refine_sketch=False,
    )

    result = agent.interpret(request, tmp_path)

    assert result.refinement_applied is False
    assert result.scene_elements
    assert result.composition_notes is not None
    assert result.preprocessing_details["steps"] == ["local-preprocess"]