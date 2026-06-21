"""Validation logic for generated runs and persisted artifacts."""

import json
from pathlib import Path

from scenografia.schemas.generation_schema import Orientation
from scenografia.schemas.validation_schema import ValidationReport
from scenografia.tools.style_validator import StyleValidator


class StyleComplianceAgent:
    """Validate scenic style compliance for generated runs."""

    def validate_text_run(self, brief: dict, prompt_package: dict, response) -> ValidationReport:
        """Create a preliminary validation report before artifacts are finalized."""
        style_contract_applied, style_issues = StyleValidator.validate_style_contract(
            prompt_package["final_prompt"]
        )
        negative_constraints_applied, negative_issues = StyleValidator.validate_negative_constraints(
            prompt_package["negative_prompt"]
        )
        issues = [*style_issues, *negative_issues]

        return ValidationReport(
            report_id=f"val_{response.request_id}",
            run_id=response.request_id,
            orientation=brief["orientation"],
            orientation_valid=prompt_package.get("orientation_applied", False),
            style_contract_applied=style_contract_applied,
            negative_constraints_applied=negative_constraints_applied,
            artifacts_complete=False,
            missing_artifacts=[],
            issues=issues,
            validation_scores={
                "style_contract": 1.0 if style_contract_applied else 0.0,
                "negative_constraints": 1.0 if negative_constraints_applied else 0.0,
            },
            recommendations=[] if not issues else ["Refine scenic style and negative constraints"],
        )

    def validate_image_path(self, image_path: Path) -> ValidationReport:
        """Validate a run by resolving its parent folder from a final image path."""
        return self.validate_run_folder(image_path.parent)

    def validate_run_folder(self, output_dir: Path) -> ValidationReport:
        """Validate a completed run folder for style, orientation, and completeness."""
        prompt = self._read_text(output_dir / "prompt.txt")
        negative_prompt = self._read_text(output_dir / "negative_prompt.txt")
        metadata = self._read_json(output_dir / "generation_response.json")

        orientation, orientation_valid, orientation_issues = self._extract_orientation(metadata)
        style_contract_applied, style_issues = StyleValidator.validate_style_contract(prompt)
        negative_constraints_applied, negative_issues = StyleValidator.validate_negative_constraints(
            negative_prompt
        )
        artifacts_complete, missing_artifacts = StyleValidator.validate_artifact_completeness(output_dir)

        issues = [*orientation_issues, *style_issues, *negative_issues]
        issues.extend(f"Missing artifact: {artifact}" for artifact in missing_artifacts)

        run_id = str(metadata.get("run_id") or output_dir.name)
        return ValidationReport(
            report_id=f"val_{run_id}",
            run_id=run_id,
            orientation=orientation,
            orientation_valid=orientation_valid,
            style_contract_applied=style_contract_applied,
            negative_constraints_applied=negative_constraints_applied,
            artifacts_complete=artifacts_complete,
            missing_artifacts=missing_artifacts,
            issues=issues,
            validation_scores={
                "style_contract": 1.0 if style_contract_applied else 0.0,
                "negative_constraints": 1.0 if negative_constraints_applied else 0.0,
                "artifact_completeness": 1.0 if artifacts_complete else 0.0,
            },
            recommendations=[] if not issues else ["Review the validation issues before reusing this run"],
        )

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _extract_orientation(metadata: dict) -> tuple[Orientation, bool, list[str]]:
        value = metadata.get("orientation")
        if value is None:
            return Orientation.SQUARE, False, ["Orientation missing from generation metadata"]
        try:
            return Orientation(str(value).lower()), True, []
        except ValueError:
            return Orientation.SQUARE, False, [f"Invalid orientation in generation metadata: {value}"]