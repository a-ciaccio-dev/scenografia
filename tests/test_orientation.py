"""Tests for orientation enum, validation, and error handling."""

import pytest
from scenografia.schemas.generation_schema import Orientation, GenerationRequest


class TestOrientationEnum:
    """Test Orientation enum."""
    
    def test_orientation_portrait_value(self):
        """Portrait orientation should have correct value."""
        assert Orientation.PORTRAIT.value == "portrait"
    
    def test_orientation_landscape_value(self):
        """Landscape orientation should have correct value."""
        assert Orientation.LANDSCAPE.value == "landscape"
    
    def test_orientation_square_value(self):
        """Square orientation should have correct value."""
        assert Orientation.SQUARE.value == "square"
    
    def test_all_orientations_exist(self):
        """All required orientations should be defined."""
        orientations = [Orientation.PORTRAIT, Orientation.LANDSCAPE, Orientation.SQUARE]
        assert len(orientations) == 3


class TestOrientationValidation:
    """Test orientation validation in schemas."""
    
    def test_generation_request_requires_orientation(self):
        """GenerationRequest must have orientation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                input_type="text",
                text_prompt="Test scene"
                # Missing orientation
            )
    
    def test_generation_request_accepts_portrait(self):
        """GenerationRequest should accept portrait orientation."""
        req = GenerationRequest(
            input_type="text",
            text_prompt="Test scene",
            orientation=Orientation.PORTRAIT
        )
        assert req.orientation == Orientation.PORTRAIT
    
    def test_generation_request_accepts_landscape(self):
        """GenerationRequest should accept landscape orientation."""
        req = GenerationRequest(
            input_type="text",
            text_prompt="Test scene",
            orientation=Orientation.LANDSCAPE
        )
        assert req.orientation == Orientation.LANDSCAPE
    
    def test_generation_request_accepts_square(self):
        """GenerationRequest should accept square orientation."""
        req = GenerationRequest(
            input_type="text",
            text_prompt="Test scene",
            orientation=Orientation.SQUARE
        )
        assert req.orientation == Orientation.SQUARE
    
    def test_generation_request_rejects_invalid_orientation(self):
        """GenerationRequest should reject invalid orientation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                input_type="text",
                text_prompt="Test scene",
                orientation="invalid"
            )


class TestOrientationPersistence:
    """Test that orientation is properly persisted."""
    
    def test_orientation_in_request_model(self):
        """Orientation should be accessible in request."""
        req = GenerationRequest(
            input_type="text",
            text_prompt="Forest scene",
            orientation=Orientation.LANDSCAPE
        )
        assert hasattr(req, "orientation")
        assert req.orientation == Orientation.LANDSCAPE
    
    def test_orientation_survives_serialization(self):
        """Orientation should survive model serialization."""
        req = GenerationRequest(
            input_type="text",
            text_prompt="Forest scene",
            orientation=Orientation.LANDSCAPE
        )
        data = req.model_dump()
        assert "orientation" in data
        assert data["orientation"] == Orientation.LANDSCAPE.value


class TestNonInteractiveOrientationFailure:
    """Test that non-interactive runs fail without orientation."""
    
    def test_missing_orientation_fails_validation(self):
        """Request without orientation should fail."""
        with pytest.raises(ValueError):
            GenerationRequest(
                input_type="text",
                text_prompt="Test"
                # No orientation - should fail
            )
    
    def test_orientation_none_fails(self):
        """None orientation should fail."""
        with pytest.raises(ValueError):
            GenerationRequest(
                input_type="text",
                text_prompt="Test",
                orientation=None
            )


class TestOrientationInBrief:
    """Test orientation in structured brief."""
    
    def test_brief_requires_orientation(self):
        """StructuredBrief must have orientation."""
        from scenografia.schemas.brief_schema import StructuredBrief
        
        with pytest.raises(ValueError):
            StructuredBrief(
                scene_description="Test scene",
                source_type="text"
                # Missing orientation
            )
    
    def test_brief_accepts_orientation(self):
        """StructuredBrief should accept orientation."""
        from scenografia.schemas.brief_schema import StructuredBrief
        
        brief = StructuredBrief(
            scene_description="Test scene",
            orientation=Orientation.LANDSCAPE,
            source_type="text"
        )
        assert brief.orientation == Orientation.LANDSCAPE
