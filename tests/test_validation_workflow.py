"""Tests for validation persistence and orientation traceability."""

import json
from pathlib import Path

from scenografia.schemas.generation_schema import GenerationMode, Orientation
from scenografia.schemas.validation_schema import GenerationMetadata, ValidationReport
from scenografia.tools.output_manager import OutputManager


class StubResponse:
    image_data = b"fake-image-bytes"
    image_url = "https://example.com/final.png"
    model_used = "demo-model"
    request_id = "req-us3-001"


def test_persist_text_run_records_orientation_in_metadata_and_validation_report(tmp_path):
    """Persisted artifacts should keep the selected orientation in metadata and report."""
    metadata = GenerationMetadata(
        run_id="req-us3-001",
        input_type="text",
        original_prompt="Painted harbor town backdrop",
        orientation=Orientation.SQUARE,
        generation_mode=GenerationMode.STANDARD,
        model_id="demo-model",
        brief={"orientation": Orientation.SQUARE},
        final_prompt="Theatrical scenic design in square format with full color and clean outlines.",
        negative_prompt="Avoid photorealism, 3D-render aesthetics, blurry edges, text, logos, or watermarks.",
        image_url="https://example.com/final.png",
    )
    validation_report = ValidationReport(
        report_id="val-us3-001",
        run_id="req-us3-001",
        orientation=Orientation.SQUARE,
        orientation_valid=True,
        style_contract_applied=True,
        negative_constraints_applied=True,
        artifacts_complete=False,
        issues=[],
    )

    OutputManager.persist_text_run(
        brief={
            "scene_description": "Painted harbor town backdrop",
            "orientation": Orientation.SQUARE,
            "generation_mode": GenerationMode.STANDARD,
            "style_constraints": ["full color with solid fills"],
            "negative_constraints": ["no photorealism"],
            "composition_guidance": ["square staging"],
            "input_source": "text",
        },
        prompt_package={
            "final_prompt": metadata.final_prompt,
            "negative_prompt": metadata.negative_prompt,
            "orientation_applied": True,
        },
        response=StubResponse(),
        validation_report=validation_report,
        metadata=metadata,
        output_dir=tmp_path,
    )

    saved_metadata = json.loads((tmp_path / "generation_response.json").read_text(encoding="utf-8"))
    saved_report = json.loads((tmp_path / "validation_report.json").read_text(encoding="utf-8"))

    assert saved_metadata["orientation"] == "square"
    assert saved_report["orientation"] == "square"
    assert saved_report["style_contract_applied"] is True
    assert saved_report["negative_constraints_applied"] is True
    assert saved_report["artifacts_complete"] is True
    assert saved_report["issues"] == []