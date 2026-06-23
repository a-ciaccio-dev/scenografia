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

    def refine_prompt_package(self, prompt_package: dict, issues: list[str]) -> dict:
        """Refine the prompt package based on validation issues."""
        final_prompt = prompt_package["final_prompt"]
        negative_prompt = prompt_package["negative_prompt"]
        
        has_missing_indicators = False
        prohibited_terms = []
        missing_negative_coverage = False
        
        for issue in issues:
            issue_lower = issue.lower()
            if "missing theatrical/scenic style indicators" in issue_lower:
                has_missing_indicators = True
            elif "contains prohibited term" in issue_lower:
                parts = issue.split(":")
                if len(parts) > 1:
                    prohibited_terms.append(parts[1].strip())
            elif "missing required scenic constraint coverage" in issue_lower or "missing or too brief" in issue_lower:
                missing_negative_coverage = True
                
        if has_missing_indicators:
            final_prompt = "Theatrical scenic design sketch of " + final_prompt
            
        for term in prohibited_terms:
            import re
            final_prompt = re.sub(re.escape(term), "", final_prompt, flags=re.IGNORECASE)
            
        if missing_negative_coverage:
            missing_rules = "photorealism, 3d, blur, text, logo, watermark, gradient, glow, airbrush"
            if negative_prompt:
                negative_prompt = negative_prompt + ", avoid " + missing_rules
            else:
                negative_prompt = "Avoid: " + missing_rules
                
        final_prompt = enforce_svg_constraints(final_prompt)
        
        return {
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "orientation_applied": prompt_package.get("orientation_applied", False)
        }