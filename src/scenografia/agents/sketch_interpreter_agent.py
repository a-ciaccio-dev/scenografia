"""Sketch interpretation orchestration for sketch-mode generation."""

from pathlib import Path
from typing import Callable

from scenografia.schemas.generation_schema import GenerationRequest
from scenografia.schemas.sketch_schema import SketchInterpretation
from scenografia.tools.image_preprocessor import SketchPreprocessor


class SketchInterpreterAgent:
    """Interpret black-and-white sketches using local preprocessing first."""

    def __init__(self, refinement_callback: Callable[[GenerationRequest, SketchInterpretation], str] | None = None):
        self.refinement_callback = refinement_callback

    def interpret(self, request: GenerationRequest, output_dir: Path) -> SketchInterpretation:
        """Preprocess a sketch, persist it, and optionally refine it."""
        if not request.sketch_path:
            raise ValueError("Sketch path is required for sketch interpretation")

        sketch_path = Path(request.sketch_path)
        original_image = SketchPreprocessor.load_sketch(sketch_path)
        processed_image = SketchPreprocessor.preprocess_sketch(sketch_path)
        if original_image is None or processed_image is None:
            raise ValueError(f"Unable to preprocess sketch: {sketch_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        processed_sketch_path = output_dir / "processed_sketch.png"
        if not SketchPreprocessor.save_processed_sketch(processed_image, processed_sketch_path):
            raise RuntimeError("Failed to save processed sketch")

        elements = SketchPreprocessor.extract_sketch_elements(processed_image)
        preprocessing_details = SketchPreprocessor.get_preprocessing_details(original_image, processed_image)
        scene_elements = self._describe_scene_elements(elements)
        composition_notes = self._build_composition_notes(elements)

        interpretation = SketchInterpretation(
            processed_sketch_path=str(processed_sketch_path),
            scene_elements=scene_elements,
            composition_notes=composition_notes,
            refinement_applied=False,
            refinement_description=None,
            preprocessing_details=preprocessing_details,
        )

        if request.refine_sketch and self.refinement_callback is not None:
            interpretation.refinement_applied = True
            interpretation.refinement_description = self.refinement_callback(request, interpretation)

        return interpretation

    @staticmethod
    def _describe_scene_elements(elements: dict) -> list[str]:
        """Convert local contour data into simple scene-element descriptions."""
        detected = elements.get("detected", [])
        if not detected:
            return ["simplified scenic forms from the supplied sketch"]

        descriptions = []
        for index, item in enumerate(detected[:3], start=1):
            size = int(item.get("size", 0))
            descriptions.append(f"major scenic shape {index} with contour area {size}")
        return descriptions

    @staticmethod
    def _build_composition_notes(elements: dict) -> str:
        """Derive a compact composition note from contour analysis."""
        count = elements.get("total_contours", 0)
        if count <= 0:
            return "Preserve the overall composition from the source sketch."
        return f"Preserve the sketch composition with {count} detected contour regions and clear focal separation."