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
        provider_type: 'antigravity' or 'openrouter' (defaults to SCENOGRAFIA_PROVIDER env or 'antigravity')
    """
    selected = (provider_type or os.getenv("SCENOGRAFIA_PROVIDER", "antigravity")).lower()
    if selected == "openrouter":
        return OpenRouterProvider()
    return AntigravityBridgeProvider()


def get_text_provider(provider_type: Optional[str] = None) -> BaseTextProvider:
    """
    Get a text provider instance.
    
    Args:
        provider_type: 'antigravity' or 'openrouter' (defaults to SCENOGRAFIA_PROVIDER env or 'antigravity')
    """
    selected = (provider_type or os.getenv("SCENOGRAFIA_PROVIDER", "antigravity")).lower()
    if selected == "openrouter":
        return OpenRouterProvider()
    return AntigravityBridgeProvider()
