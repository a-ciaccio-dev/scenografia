"""
Prompt template primitives and scenic constraint helpers.

Provides reusable prompt composition functions for scenic design generation
with style compliance enforcement.
"""

from typing import List, Tuple
from ..schemas.generation_schema import Orientation


# Scenic style requirements
SCENIC_STYLE_REQUIREMENTS = [
    "full color with solid fills",
    "hand-drawn or hand-painted theatrical scenic look",
    "clean outlines and closed paths",
    "suitable for SVG vectorization",
    "optimized for theatrical printing and digital projection",
    "layer separation in mind for future SVG export",
    "vector-like drawing",
    "flat colors",
    "solid color areas",
    "simple shapes",
    "clear separation between elements",
    "high contrast edges"
]

# Scenic style prohibitions
SCENIC_STYLE_PROHIBITIONS = [
    "photorealism",
    "photographic rendering",
    "3D-render aesthetics",
    "blurry edges",
    "excessive micro-details",
    "unreadable shape noise",
    "gradients",
    "complex textures",
    "digital glow",
    "airbrush effects",
    "text, logos, or watermarks",
    "captions"
]

BASE_PROMPT = """Create a theatrical scenic design sketch with these characteristics:
- theatrical scenic design sketch
- vector-like drawing
- clean outlines
- flat colors
- solid color areas
- simple shapes
- clear separation between elements
- high contrast edges
- hand-drawn scenic design look
- suitable for SVG vectorization and layer separation"""

BASE_NEGATIVE = """Avoid: photorealism, photographic rendering, gradients, complex textures, text, watermark, logos, captions, 3D-render aesthetics, blurry edges, excessive micro-details, airbrush, digital glow, unreadable shape noise."""


# Orientation descriptions
ORIENTATION_DESCRIPTIONS = {
    Orientation.PORTRAIT: "portrait orientation (taller than wide)",
    Orientation.LANDSCAPE: "landscape orientation (wider than tall)",
    Orientation.SQUARE: "square format"
}


def enforce_svg_constraints(prompt: str) -> str:
    """Ensure that the final prompt always contains the fundamental SVG-safe constraints."""
    required_phrases = [
        "theatrical scenic design sketch",
        "vector-like drawing",
        "clean outlines",
        "flat colors",
        "solid color areas",
        "simple shapes",
        "clear separation between elements",
        "high contrast edges",
        "hand-drawn scenic design look"
    ]
    prompt_lower = prompt.lower()
    missing_phrases = [p for p in required_phrases if p not in prompt_lower]
    if missing_phrases:
        prompt = prompt + "\nSVG-safe constraints: " + ", ".join(missing_phrases)
    return prompt


def build_scenic_constraint_prompt() -> str:
    """
    Build the scenic style constraint portion of the prompt.
    
    Returns:
        Constraint prompt text
    """
    requirements = ", ".join(SCENIC_STYLE_REQUIREMENTS)
    prohibitions = ", ".join(SCENIC_STYLE_PROHIBITIONS)
    
    return f"""Create a theatrical scenic design with these characteristics:
- {requirements}
 
Avoid:
- {prohibitions}"""


def build_orientation_prompt(orientation: Orientation) -> str:
    """
    Build orientation-specific prompt guidance.
    
    Args:
        orientation: Target orientation
        
    Returns:
        Orientation guidance text
    """
    description = ORIENTATION_DESCRIPTIONS.get(
        orientation,
        "with appropriate aspect ratio"
    )
    return f"Design in {description}."


def build_final_prompt(
    base_prompt: str,
    orientation: Orientation,
    style_guidance: str = None,
    user_style: dict = None
) -> str:
    """
    Compose the complete final prompt for generation.
    
    Args:
        base_prompt: User's original prompt or scene description
        orientation: Target orientation
        style_guidance: Optional style direction (backward compatibility)
        user_style: Selected User Style dictionary
        
    Returns:
        Complete final prompt
    """
    from scenografia.styles.loader import load_style_by_name
    
    # Load user style
    style_dict = user_style
    if style_dict is None:
        style_dict = load_style_by_name("Default")
        
    prompt_additions = style_dict.get("prompt_additions", "")
    
    # Build prompt composition: BASE_PROMPT + style prompt_additions + base_prompt (brief_text)
    parts = [BASE_PROMPT]
    if prompt_additions:
        parts.append(prompt_additions)
        
    parts.append(base_prompt)
    if style_guidance and style_guidance not in base_prompt:
        parts.append(f"Style context: {style_guidance}")
        
    parts.append(build_orientation_prompt(orientation))
    
    final_prompt = "\n".join(parts)
    return enforce_svg_constraints(final_prompt)


def build_negative_prompt(user_style: dict = None) -> str:
    """
    Build the negative prompt (constraints) for generation.
    
    Returns:
        Negative prompt text
    """
    from scenografia.styles.loader import load_style_by_name
    
    style_dict = user_style
    if style_dict is None:
        style_dict = load_style_by_name("Default")
        
    negative_additions = style_dict.get("negative_additions", "")
    
    parts = [BASE_NEGATIVE]
    if negative_additions:
        parts.append(negative_additions)
        
    return "\n".join(parts)


def validate_prompt_contains_scenic_style(prompt: str) -> Tuple[bool, List[str]]:
    """
    Validate that a prompt contains expected scenic style references.
    
    Args:
        prompt: Prompt text to validate
        
    Returns:
        Tuple of (is_valid, missing_keywords)
    """
    prompt_lower = prompt.lower()
    missing = []
    
    # Check for key scenic style indicators
    key_indicators = [
        ("theatrical", "theatrical reference"),
        ("scenic", "scenic reference"),
        ("stage", "stage reference"),
        ("design", "design reference"),
    ]
    
    found = False
    for keyword, description in key_indicators:
        if keyword in prompt_lower:
            found = True
            break
    
    if not found:
        missing.append("No theatrical/scenic/stage/design reference")
    
    # Check that it doesn't contain prohibition keywords
    for prohibition in ["photorealism", "photorealistic", "3d render", "photograph"]:
        if prohibition in prompt_lower:
            missing.append(f"Contains prohibition: {prohibition}")
    
    return len(missing) == 0, missing


def apply_orientation_to_prompt(prompt: str, orientation: Orientation) -> str:
    """
    Inject orientation requirement into existing prompt if not present.
    
    Args:
        prompt: Existing prompt
        orientation: Target orientation
        
    Returns:
        Updated prompt with orientation
    """
    orientation_text = build_orientation_prompt(orientation)
    if orientation_text not in prompt:
        return f"{prompt} {orientation_text}"
    return prompt

