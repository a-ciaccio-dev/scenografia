"""Text and sketch input normalization into structured briefs."""

from scenografia.schemas.generation_schema import GenerationRequest
from scenografia.schemas.sketch_schema import SketchInterpretation
from scenografia.schemas.brief_schema import StructuredBrief


class BriefAgent:
    """Create structured briefs from validated generation requests."""

    def create_from_text(self, request: GenerationRequest) -> StructuredBrief:
        """Build a structured brief for text-mode generation."""
        if not request.text_prompt:
            raise ValueError("Text prompt is required for text-mode generation")

        return StructuredBrief(
            scene_description=request.text_prompt.strip(),
            orientation=request.orientation,
            generation_mode=request.mode,
            source_type="text",
            input_source="text",
            style_constraints=[
                "full color with solid fills",
                "hand-drawn or hand-painted theatrical scenic look",
                "clean outlines and closed paths",
                "suitable for SVG vectorization",
            ],
            negative_constraints=[
                "no photorealism",
                "no gradients",
                "no digital glow",
                "no airbrush effects",
                "no text, logos, or watermarks",
            ],
            composition_guidance=[
                f"compose for {request.orientation.value} orientation",
                "preserve clear theatrical staging and readable depth",
            ],
            style_guidance=request.style_guidance,
            selected_style=getattr(request, "selected_style", "Default"),
        )

    def create_from_sketch(
        self,
        request: GenerationRequest,
        interpretation: SketchInterpretation,
    ) -> StructuredBrief:
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

        return StructuredBrief(
            scene_description=scene_description,
            orientation=request.orientation,
            generation_mode=request.mode,
            source_type="sketch",
            input_source="sketch",
            style_constraints=[
                "full color with solid fills",
                "hand-drawn or hand-painted theatrical scenic look",
                "clean outlines and closed paths",
                "suitable for SVG vectorization",
                f"respect style guidance: {style_guidance}",
            ],
            negative_constraints=[
                "no photorealism",
                "no gradients",
                "no digital glow",
                "no airbrush effects",
                "no text, logos, or watermarks",
            ],
            composition_guidance=[
                f"compose for {request.orientation.value} orientation",
                interpretation.composition_notes or "preserve the sketched scene layout",
            ],
            style_guidance=style_guidance,
            processed_sketch_path=interpretation.processed_sketch_path,
            refinement_applied=interpretation.refinement_applied,
            selected_style=getattr(request, "selected_style", "Default"),
        )
