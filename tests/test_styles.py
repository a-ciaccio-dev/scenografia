import pytest
import json
from pathlib import Path
from scenografia.styles.loader import (
    load_styles,
    load_style_by_name,
    save_style,
    sanitize_filename,
    STYLES_DIR
)
from scenografia.tools.prompt_templates import (
    build_final_prompt,
    build_negative_prompt,
    enforce_svg_constraints,
    BASE_PROMPT,
    BASE_NEGATIVE
)
from scenografia.schemas.generation_schema import Orientation


def test_sanitize_filename():
    assert sanitize_filename("Minimal") == "minimal.json"
    assert sanitize_filename("Espressionista Style!") == "espressionista_style.json"
    assert sanitize_filename("   My Custom Style  ") == "my_custom_style.json"
    with pytest.raises(ValueError):
        sanitize_filename("")
    with pytest.raises(ValueError):
        sanitize_filename("   ")


def test_load_styles():
    styles = load_styles()
    assert len(styles) >= 3
    names = [s["name"].lower() for s in styles]
    assert "default" in names
    assert "minimal" in names
    assert "espressionista" in names


def test_load_style_by_name():
    # Test valid style loading
    minimal = load_style_by_name("Minimal")
    assert minimal["name"] == "Minimal"
    assert "minimal stage composition" in minimal["prompt_additions"]

    # Test case insensitivity
    espressionista = load_style_by_name("espressionista")
    assert espressionista["name"] == "Espressionista"

    # Test fallback to Default
    fallback = load_style_by_name("NonExistentStyleXYZ")
    assert fallback["name"] == "Default"


def test_save_style(tmp_path, monkeypatch):
    # Mock STYLES_DIR to use a temporary path
    monkeypatch.setattr("scenografia.styles.loader.STYLES_DIR", tmp_path)
    monkeypatch.setattr("scenografia.styles.loader.load_styles", lambda: [])
    
    new_style = {
        "name": "SciFi Gothic",
        "description": "stile gotico fantascientifico",
        "prompt_additions": "neon lights, cathedral arches, holographic projection",
        "negative_additions": "nature, trees, bright sunlight"
    }

    save_style(new_style)

    expected_file = tmp_path / "scifi_gothic.json"
    assert expected_file.exists()

    with open(expected_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["name"] == "SciFi Gothic"
    assert saved_data["prompt_additions"] == "neon lights, cathedral arches, holographic projection"


def test_enforce_svg_constraints():
    prompt_without_constraints = "A futuristic city in space with skyscrapers and spaceships"
    enforced = enforce_svg_constraints(prompt_without_constraints)
    
    # Assert missing phrases were added
    assert "SVG-safe constraints:" in enforced
    assert "theatrical scenic design sketch" in enforced.lower()
    assert "vector-like drawing" in enforced.lower()

    # If constraints are already present, they shouldn't be added again or cause issues
    already_good = "theatrical scenic design sketch vector-like drawing clean outlines flat colors solid color areas simple shapes clear separation between elements high contrast edges hand-drawn scenic design look"
    enforced_already_good = enforce_svg_constraints(already_good)
    assert "SVG-safe constraints:" not in enforced_already_good


def test_build_final_prompt_with_styles():
    brief_text = "A dark dungeon room"
    orientation = Orientation.LANDSCAPE

    # Test with Default style
    default_prompt = build_final_prompt(brief_text, orientation, user_style=None)
    assert BASE_PROMPT in default_prompt
    assert brief_text in default_prompt

    # Test with Minimal style
    minimal_style = load_style_by_name("Minimal")
    minimal_prompt = build_final_prompt(brief_text, orientation, user_style=minimal_style)
    assert BASE_PROMPT in minimal_prompt
    assert "minimal stage composition" in minimal_prompt
    assert brief_text in minimal_prompt

    # Test that SVG constraints are always enforced at the end
    assert "clean outlines" in minimal_prompt.lower()
