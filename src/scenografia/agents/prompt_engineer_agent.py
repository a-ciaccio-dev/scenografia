"""Prompt composition for scenic image generation."""

from scenografia.tools.prompt_templates import build_final_prompt, build_negative_prompt


class PromptEngineerAgent:
    """Compose the final prompt package from a structured brief."""

    def build_prompt_package(self, brief: dict) -> dict:
        """Build final and negative prompts for generation."""
        style_guidance = brief.get("style_guidance")
        if not style_guidance:
            style_guidance = "; ".join(brief.get("style_constraints", []))

        final_prompt = build_final_prompt(
            base_prompt=brief["scene_description"],
            orientation=brief["orientation"],
            style_guidance=style_guidance,
        )
        negative_prompt = build_negative_prompt()
        return {
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "orientation_applied": brief["orientation"].value in final_prompt.lower(),
        }