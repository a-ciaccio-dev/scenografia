"""Text and sketch input normalization into structured briefs."""

from scenografia.schemas.generation_schema import GenerationRequest
from scenografia.schemas.sketch_schema import SketchInterpretation


class BriefAgent:
    """Create structured briefs from validated generation requests."""

    def create_from_text(self, request: GenerationRequest) -> dict:
        """Build a structured brief for text-mode generation."""
        if not request.text_prompt:
            raise ValueError("Text prompt is required for text-mode generation")

        return {
            "scene_description": request.text_prompt.strip(),
            "orientation": request.orientation,
            "generation_mode": request.mode,
            "style_constraints": [
                "full color with solid fills",
                "hand-drawn or hand-painted theatrical scenic look",
                "clean outlines and closed paths",
                "suitable for SVG vectorization",
            ],
            "negative_constraints": [
                "no photorealism",
                "no gradients",
                "no digital glow",
                "no airbrush effects",
                "no text, logos, or watermarks",
            ],
            "composition_guidance": [
                f"compose for {request.orientation.value} orientation",
                "preserve clear theatrical staging and readable depth",
            ],
            "input_source": "text",
            "style_guidance": request.style_guidance,
        }

    def create_from_sketch(
        self,
        request: GenerationRequest,
        interpretation: SketchInterpretation,
    ) -> dict:
        """Build a structured brief for sketch-mode generation."""
        style_guidance = request.style_guidance or "theatrical scenic backdrop"
        scene_bits = list(interpretation.scene_elements)
        if interpretation.composition_notes:
            scene_bits.append(interpretation.composition_notes)
        if interpretation.refinement_description:
            scene_bits.append(interpretation.refinement_description)

        scene_description = "; ".join(bit for bit in scene_bits if bit).strip()
        if not scene_description:
            scene_description = "theatrical scenic composition derived from a black-and-white sketch"

        return {
            "scene_description": scene_description,
            "orientation": request.orientation,
            "generation_mode": request.mode,
            "style_constraints": [
                "full color with solid fills",
                "hand-drawn or hand-painted theatrical scenic look",
                "clean outlines and closed paths",
                "suitable for SVG vectorization",
                f"respect style guidance: {style_guidance}",
            ],
            "negative_constraints": [
                "no photorealism",
                "no gradients",
                "no digital glow",
                "no airbrush effects",
                "no text, logos, or watermarks",
            ],
            "composition_guidance": [
                f"compose for {request.orientation.value} orientation",
                interpretation.composition_notes or "preserve the sketched scene layout",
            ],
            "input_source": "sketch",
            "style_guidance": style_guidance,
            "processed_sketch_path": interpretation.processed_sketch_path,
            "refinement_applied": interpretation.refinement_applied,
        }