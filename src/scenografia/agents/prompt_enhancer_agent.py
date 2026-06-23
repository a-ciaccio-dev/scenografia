"""Agent for enhancing simple prompts into detailed theatrical scene descriptions."""

from typing import Optional
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.config import Config


class PromptEnhancerAgent:
    """Enhance a user's simple scenic description into a rich theatrical prompt."""

    def __init__(self, client: Optional[OpenRouterClient] = None):
        self.client = client or OpenRouterClient()

    def enhance_prompt(
        self,
        raw_prompt: str,
        model_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        division: Optional[str] = "Nessuna"
    ) -> str:
        """
        Rewrite raw prompt into a rich, detailed theatrical scene description.
        
        Args:
            raw_prompt: Simple user scenic idea
            model_id: Optional model override (defaults to configured enhancer model)
            image_bytes: Optional reference image bytes to analyze (Vision)
            division: Optional subdivision type ("Nessuna", "2 parti", "3 parti", "4 parti")
            
        Returns:
            Enhanced scenic description
        """
        if not raw_prompt or not raw_prompt.strip():
            return ""

        model = model_id or Config.OPENROUTER_ENHANCER_MODEL or "google/gemini-2.5-flash"
        
        division_rule = ""
        if division == "2 parti":
            division_rule = (
                "\nADDITIONAL RULE: The user requested a layout divided into 2 sections. "
                "Structure the scenic layout as divided into two symmetrical halves separated by a central vertical element (like a tree, rock, beam, pipe) acting as a visual boundary, and describe Left and Right sections."
            )
        elif division == "3 parti":
            division_rule = (
                "\nADDITIONAL RULE: The user requested a layout divided into 3 panels. "
                "Structure the scenic layout as divided into 3 equal vertical panels separated by vertical elements acting as visual boundaries, and describe all three sections."
            )
        elif division == "4 parti":
            division_rule = (
                "\nADDITIONAL RULE: The user requested a layout divided into 4 panels. "
                "Structure the scenic layout as divided into 4 equal vertical panels separated by vertical elements acting as visual boundaries, and describe all four sections."
            )

        system_instruction = (
            "You are a theatrical scenic designer and AI prompt engineering expert.\n"
            "Your task is to rewrite the user's simple scenic concept into a highly structured, "
            "detailed prompt specification for generating a theatrical backdrop.\n\n"
            "Strictly adhere to the following formatting rules:\n"
            "1. Start with a title header using the 🎨 emoji: "
            "'🎨 DATI TECNICI – FONDALE TEATRALE: [UPPERCASE NAME OF THE SCENE]' "
            "or '🎨 PROMPT PER GENERARE UN FONDALE TEATRALE [UPPERCASE NAME OF THE SCENE] COLORATO IN FORMATO PNG (CONVERTIBILE IN SVG)'.\n"
            "2. Organize the prompt into clear, thematic sections using Markdown headings and specific emojis (e.g., 📐, 🧱, 🌳, 🛖, 🌿, 🐾, 🕯️, 🔧, 🛠️).\n"
            "3. Structure each section with clean bullet points describing concrete, visual details (layout, composition, elements, textures, colors).\n"
            "4. Enforce the theatrical and vector-safe constraints: specify a 16:9 horizontal layout, "
            "flat and solid colors, clean outlines, closed paths, no gradients, no soft shading, no digital glow or airbrush, suitable for vector conversion (SVG).\n"
            "5. Do NOT divide the scene into parts, panels, or halves, nor enforce a central vertical boundary, unless a specific divided layout is requested. By default, describe a single unified theatrical scene composition.\n"
            "6. Detail specific scenic sections, architectural elements, natural details, atmospheric details, and color palettes.\n"
            "7. Output ONLY the markdown formatted specification. Do not include any introductory remarks, explanations, conversational filler, or surrounding quotes."
            + division_rule
        )

        user_prompt = raw_prompt.strip()
        if image_bytes:
            user_prompt = (
                "Analyze the style, composition, colors, and objects of the attached image. "
                f"Incorporate these characteristics and merge them with this scenic concept to create the enhanced prompt: {user_prompt}"
            )

        try:
            enhanced = self.client.generate_text(
                prompt=user_prompt,
                system_instruction=system_instruction,
                model_id=model,
                image_bytes=image_bytes,
            )
            return enhanced.strip().strip('"').strip("'")
        except Exception as e:
            # Fallback to the original prompt if API call fails
            return raw_prompt
