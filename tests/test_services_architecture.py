"""Unit tests verifying the Service Layer modular architecture."""

def test_services_package_exports():
    """Verify that TextGenerationService and SketchGenerationService are exported by services."""
    from scenografia.services import TextGenerationService, SketchGenerationService
    assert TextGenerationService is not None
    assert SketchGenerationService is not None


def test_agent_module_backwards_compatibility_reexports():
    """Verify backwards compatibility of imports from agents.image_generation_agent."""
    from scenografia.agents.image_generation_agent import (
        TextGenerationService as LegacyTextService,
        SketchGenerationService as LegacySketchService,
        ImageGenerationAgent,
    )
    from scenografia.services import TextGenerationService, SketchGenerationService

    assert LegacyTextService is TextGenerationService
    assert LegacySketchService is SketchGenerationService
    assert ImageGenerationAgent is not None
