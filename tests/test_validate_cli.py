"""Tests for the validate CLI command."""

import json
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from scenografia.main import app


runner = CliRunner()


def _create_run_folder(base_dir: Path, *, complete: bool = True) -> Path:
    run_dir = base_dir / "2026-06-21_2000_example-scene"
    run_dir.mkdir()
    Image.new("RGB", (640, 480), color="green").save(run_dir / "final.png")
    (run_dir / "prompt.txt").write_text(
        "Theatrical scenic design with full color, solid fills, and clean outlines.",
        encoding="utf-8",
    )
    (run_dir / "negative_prompt.txt").write_text(
        "Avoid photorealism, 3D-render aesthetics, blurry edges, text, logos, or watermarks.",
        encoding="utf-8",
    )
    (run_dir / "generation_response.json").write_text(
        json.dumps({"run_id": "run-validate-001", "orientation": "landscape"}),
        encoding="utf-8",
    )
    if complete:
        (run_dir / "brief.json").write_text("{}", encoding="utf-8")
        (run_dir / "validation_report.json").write_text("{}", encoding="utf-8")
    return run_dir


def test_validate_command_accepts_image_path_and_updates_report(tmp_path):
    """Validate should infer the run folder from final.png and persist a structured report."""
    run_dir = _create_run_folder(tmp_path, complete=True)

    result = runner.invoke(app, ["validate", "--image", str(run_dir / "final.png")])

    assert result.exit_code == 0
    saved_report = json.loads((run_dir / "validation_report.json").read_text(encoding="utf-8"))
    assert saved_report["orientation"] == "landscape"
    assert saved_report["style_contract_applied"] is True
    assert saved_report["negative_constraints_applied"] is True
    assert saved_report["artifacts_complete"] is True
    assert saved_report["issues"] == []
    assert "validation_report.json" in result.stdout


def test_validate_command_supports_run_folder_and_reports_missing_artifacts(tmp_path):
    """Validate should accept a run folder directly and fail visibly on incomplete artifacts."""
    run_dir = _create_run_folder(tmp_path, complete=False)

    result = runner.invoke(app, ["validate", "--run", str(run_dir)])

    assert result.exit_code == 1
    saved_report = json.loads((run_dir / "validation_report.json").read_text(encoding="utf-8"))
    assert saved_report["artifacts_complete"] is False
    assert any("brief.json" in issue for issue in saved_report["issues"])
    assert "brief.json" in result.stdout