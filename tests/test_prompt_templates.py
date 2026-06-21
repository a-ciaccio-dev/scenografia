"""Tests for prompt templates and scenic style contract."""

import pytest
from scenografia.tools.prompt_templates import (
    build_scenic_constraint_prompt,
    build_orientation_prompt,
    build_final_prompt,
    build_negative_prompt,
    validate_prompt_contains_scenic_style,
    apply_orientation_to_prompt,
    SCENIC_STYLE_REQUIREMENTS,
    SCENIC_STYLE_PROHIBITIONS,
)
from scenografia.schemas.generation_schema import Orientation


class TestScenicConstraintPrompt:
    """Test scenic style constraint prompt building."""
    
    def test_constraint_prompt_includes_requirements(self):
        """Constraint prompt should include scenic requirements."""
        prompt = build_scenic_constraint_prompt()
        assert "theatrical" in prompt.lower()
        assert len(prompt) > 50  # Should be substantial
    
    def test_constraint_prompt_excludes_prohibitions(self):
        """Constraint prompt should list prohibitions."""
        prompt = build_scenic_constraint_prompt()
        prompt_lower = prompt.lower()
        assert "avoid" in prompt_lower or "photorealism" in prompt_lower
    
    def test_constraint_prompt_consistency(self):
        """Multiple calls should return consistent prompts."""
        prompt1 = build_scenic_constraint_prompt()
        prompt2 = build_scenic_constraint_prompt()
        assert prompt1 == prompt2


class TestOrientationPrompt:
    """Test orientation-specific prompt generation."""
    
    def test_portrait_orientation_prompt(self):
        """Portrait prompt should reference vertical orientation."""
        prompt = build_orientation_prompt(Orientation.PORTRAIT)
        assert "portrait" in prompt.lower()
    
    def test_landscape_orientation_prompt(self):
        """Landscape prompt should reference horizontal orientation."""
        prompt = build_orientation_prompt(Orientation.LANDSCAPE)
        assert "landscape" in prompt.lower()
    
    def test_square_orientation_prompt(self):
        """Square prompt should reference square format."""
        prompt = build_orientation_prompt(Orientation.SQUARE)
        assert "square" in prompt.lower()


class TestFinalPrompt:
    """Test final prompt composition."""
    
    def test_final_prompt_includes_base(self):
        """Final prompt should include base prompt."""
        base = "A mystical forest"
        prompt = build_final_prompt(base, Orientation.LANDSCAPE)
        assert base in prompt
    
    def test_final_prompt_includes_orientation(self):
        """Final prompt should include orientation."""
        prompt = build_final_prompt("Forest", Orientation.PORTRAIT)
        assert "portrait" in prompt.lower()
    
    def test_final_prompt_includes_constraints(self):
        """Final prompt should include scenic constraints."""
        prompt = build_final_prompt("Forest", Orientation.LANDSCAPE)
        assert "theatrical" in prompt.lower() or "scenic" in prompt.lower()
    
    def test_final_prompt_with_style_guidance(self):
        """Final prompt should include style guidance when provided."""
        base = "A forest"
        style = "fairytale"
        prompt = build_final_prompt(base, Orientation.LANDSCAPE, style)
        assert style in prompt.lower()


class TestNegativePrompt:
    """Test negative prompt generation."""
    
    def test_negative_prompt_contains_prohibitions(self):
        """Negative prompt should list style prohibitions."""
        prompt = build_negative_prompt()
        prompt_lower = prompt.lower()
        
        # Should contain at least some prohibitions
        has_prohibition = any(
            p in prompt_lower
            for p in ["photorealism", "3d", "gradient", "blur"]
        )
        assert has_prohibition
    
    def test_negative_prompt_non_empty(self):
        """Negative prompt should not be empty."""
        prompt = build_negative_prompt()
        assert len(prompt) > 10


class TestPromptValidation:
    """Test prompt validation for scenic style compliance."""
    
    def test_valid_theatrical_prompt(self):
        """Theatrical prompt should be valid."""
        prompt = "A dramatic theatrical backdrop with ancient stone pillars"
        is_valid, missing = validate_prompt_contains_scenic_style(prompt)
        assert is_valid, f"Prompt should be valid but got: {missing}"
    
    def test_valid_scenic_prompt(self):
        """Scenic design prompt should be valid."""
        prompt = "A scenic design with forest elements and magical lighting"
        is_valid, missing = validate_prompt_contains_scenic_style(prompt)
        assert is_valid
    
    def test_invalid_prompt_without_indicators(self):
        """Prompt without scenic indicators should be invalid."""
        prompt = "A nice landscape painting"
        is_valid, missing = validate_prompt_contains_scenic_style(prompt)
        assert not is_valid
        assert len(missing) > 0
    
    def test_invalid_prompt_with_photorealism(self):
        """Prompt with photorealism should be invalid."""
        prompt = "A photorealistic theatrical scene"
        is_valid, missing = validate_prompt_contains_scenic_style(prompt)
        assert not is_valid
        assert "photorealistic" in str(missing).lower()


class TestOrientationApplication:
    """Test applying orientation to prompts."""
    
    def test_apply_orientation_adds_missing(self):
        """Should add orientation to prompt missing it."""
        base = "A forest scene"
        result = apply_orientation_to_prompt(base, Orientation.LANDSCAPE)
        assert "landscape" in result.lower()
        assert base in result
    
    def test_apply_orientation_no_duplicate(self):
        """Should not duplicate orientation in prompt."""
        base = "Design in landscape orientation. A forest scene"
        result = apply_orientation_to_prompt(base, Orientation.LANDSCAPE)
        # Count occurrences of "landscape"
        count = result.lower().count("landscape")
        assert count <= 2  # Maybe one original, one from function


class TestScenicStyleConstants:
    """Test scenic style constant definitions."""
    
    def test_scenic_requirements_non_empty(self):
        """Should have scenic requirements defined."""
        assert len(SCENIC_STYLE_REQUIREMENTS) > 0
        assert all(isinstance(r, str) for r in SCENIC_STYLE_REQUIREMENTS)
    
    def test_scenic_prohibitions_non_empty(self):
        """Should have scenic prohibitions defined."""
        assert len(SCENIC_STYLE_PROHIBITIONS) > 0
        assert all(isinstance(p, str) for p in SCENIC_STYLE_PROHIBITIONS)
    
    def test_no_overlap_requirements_prohibitions(self):
        """Requirements and prohibitions should not overlap."""
        req_set = set(r.lower() for r in SCENIC_STYLE_REQUIREMENTS)
        prohib_set = set(p.lower() for p in SCENIC_STYLE_PROHIBITIONS)
        overlap = req_set & prohib_set
        assert len(overlap) == 0, f"Overlap found: {overlap}"
