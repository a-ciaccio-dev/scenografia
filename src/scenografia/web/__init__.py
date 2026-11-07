"""
Web UI components package for Scenografia.
"""

from scenografia.web.history_gallery import render_history_gallery
from scenografia.web.prompt_editor import render_text_mode_inputs
from scenografia.web.results_view import display_generation_results, on_regenerate
from scenografia.web.sidebar import render_sidebar_settings

__all__ = [
    "render_sidebar_settings",
    "render_text_mode_inputs",
    "display_generation_results",
    "on_regenerate",
    "render_history_gallery",
]
