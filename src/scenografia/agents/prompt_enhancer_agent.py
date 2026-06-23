"""Agent for enhancing simple prompts into detailed theatrical scene descriptions."""

from typing import Optional
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.config import Config


class PromptEnhancerAgent:
    """Enhance a user's simple scenic description into a rich theatrical prompt."""

    def __init__(self, client: Optional[OpenRouterClient] = None):
        self.client = client or OpenRouterClient()

    def enhance_prompt(self, raw_prompt: str, model_id: Optional[str] = None) -> str:
        """
        Rewrite raw prompt into a rich, detailed theatrical scene description.
        
        Args:
            raw_prompt: Simple user scenic idea
            model_id: Optional model override (defaults to configured enhancer model)
            
        Returns:
            Enhanced scenic description
        """
        if not raw_prompt or not raw_prompt.strip():
            return ""

        model = model_id or Config.OPENROUTER_ENHANCER_MODEL or "google/gemini-2.5-flash"
        
        system_instruction = (
            "You are a theatrical scenic designer and AI prompt engineering expert. "
            "Your task is to rewrite the user's simple scenic concept into a detailed, "
            "rich theatrical scene description (about 2-4 sentences). "
            "Focus on composition, lighting, materials, depth, and atmospheric mood. "
            "Strictly avoid any quality buzzwords (e.g., 'hyperrealistic', '4k', 'detailed') "
            "and photorealistic rendering tags. Ensure it remains suitable for flat colors, "
            "clean outlines, and subsequent vectorization (SVG export). "
            "Output ONLY the enhanced description without any explanations, conversational filler, "
            "or quotes."
        )

        try:
            enhanced = self.client.generate_text(
                prompt=raw_prompt.strip(),
                system_instruction=system_instruction,
                model_id=model,
            )
            return enhanced.strip().strip('"').strip("'")
        except Exception as e:
            # Fallback to the original prompt if API call fails
            return raw_prompt
