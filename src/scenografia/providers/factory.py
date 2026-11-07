"""
Provider factory for acquiring image and text generation providers.
"""

import os
from typing import Optional
from scenografia.providers.base import BaseImageProvider, BaseTextProvider
from scenografia.providers.openrouter_provider import OpenRouterProvider
from scenografia.providers.antigravity_bridge import AntigravityBridgeProvider


def get_image_provider(provider_type: Optional[str] = None) -> BaseImageProvider:
    """
    Get an image provider instance.
    
    Args:
        provider_type: 'openrouter' or 'antigravity' (defaults to SCENOGRAFIA_PROVIDER env or 'openrouter')
    """
    selected = (provider_type or os.getenv("SCENOGRAFIA_PROVIDER", "openrouter")).lower()
    if selected in ("antigravity", "bridge", "local"):
        return AntigravityBridgeProvider()
    return OpenRouterProvider()


def get_text_provider(provider_type: Optional[str] = None) -> BaseTextProvider:
    """
    Get a text provider instance.
    
    Args:
        provider_type: 'openrouter' or 'antigravity' (defaults to SCENOGRAFIA_PROVIDER env or 'openrouter')
    """
    selected = (provider_type or os.getenv("SCENOGRAFIA_PROVIDER", "openrouter")).lower()
    if selected in ("antigravity", "bridge", "local"):
        return AntigravityBridgeProvider()
    return OpenRouterProvider()
