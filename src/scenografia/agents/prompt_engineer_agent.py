from scenografia.tools.prompt_templates import build_final_prompt, build_negative_prompt, enforce_svg_constraints
from scenografia.styles.loader import load_style_by_name


class PromptEngineerAgent:
    """Compose the final prompt package from a structured brief."""

    def enforce_svg_constraints(self, prompt: str) -> str:
        """Ensure that the prompt contains the fundamental SVG-safe constraints."""
        return enforce_svg_constraints(prompt)

    def build_prompt_package(self, brief: dict) -> dict:
        """Build final and negative prompts for generation."""
        style_guidance = brief.get("style_guidance")
        if not style_guidance:
            style_guidance = "; ".join(brief.get("style_constraints", []))

        style_name = brief.get("selected_style", "Default")
        user_style = load_style_by_name(style_name)

        final_prompt = build_final_prompt(
            base_prompt=brief["scene_description"],
            orientation=brief["orientation"],
            style_guidance=style_guidance,
            user_style=user_style,
        )
        negative_prompt = build_negative_prompt(user_style=user_style)
        return {
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "orientation_applied": brief["orientation"].value in final_prompt.lower(),
        }