"""Unit tests for AI providers and provider factory."""

from scenografia.providers.base import BaseImageProvider, BaseTextProvider
from scenografia.providers.openrouter_provider import OpenRouterProvider
from scenografia.providers.antigravity_bridge import AntigravityBridgeProvider
from scenografia.providers.factory import get_image_provider, get_text_provider
from scenografia.schemas.generation_schema import Orientation


def test_openrouter_provider_implements_protocols():
    """Verify OpenRouterProvider implements both image and text protocols."""
    provider = OpenRouterProvider()
    assert isinstance(provider, BaseImageProvider)
    assert isinstance(provider, BaseTextProvider)


def test_antigravity_bridge_provider_implements_protocols():
    """Verify AntigravityBridgeProvider implements both image and text protocols."""
    bridge = AntigravityBridgeProvider()
    assert isinstance(bridge, BaseImageProvider)
    assert isinstance(bridge, BaseTextProvider)


def test_antigravity_bridge_offline_image_generation():
    """Verify AntigravityBridgeProvider can generate a valid scenic canvas offline."""
    bridge = AntigravityBridgeProvider()
    response = bridge.generate_image(
        prompt="Theatrical forest backdrop",
        orientation=Orientation.LANDSCAPE
    )
    assert response.image_data is not None
    assert len(response.image_data) > 0
    assert response.error is None
    assert "antigravity" in response.model_used


def test_antigravity_bridge_offline_text_generation():
    """Verify AntigravityBridgeProvider can generate a structured prompt offline."""
    bridge = AntigravityBridgeProvider()
    text = bridge.generate_text(prompt="Bosco Incantato")
    assert "🎨 DATI TECNICI" in text
    assert "BOSCO INCANTATO" in text


def test_provider_factory_selection():
    """Verify factory returns appropriate provider based on provider_type."""
    openrouter = get_image_provider("openrouter")
    assert isinstance(openrouter, OpenRouterProvider)

    ag_provider = get_image_provider("antigravity")
    assert isinstance(ag_provider, AntigravityBridgeProvider)

    ag_text = get_text_provider("antigravity")
    assert isinstance(ag_text, AntigravityBridgeProvider)

def test_provider_factory_defaults_to_antigravity():
    """Verify factory returns AntigravityBridgeProvider by default with no env override."""
    import os
    orig = os.environ.pop("SCENOGRAFIA_PROVIDER", None)
    try:
        assert isinstance(get_image_provider(), AntigravityBridgeProvider)
        assert isinstance(get_text_provider(), AntigravityBridgeProvider)
    finally:
        if orig:
            os.environ["SCENOGRAFIA_PROVIDER"] = orig
