"""
Unit tests for modular Web UI components (scenografia.web).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class MockSessionState(dict):
    """Mock Streamlit session_state supporting both attribute and dict syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


def test_web_package_exports():
    """Verify that scenografia.web exports the expected modular components."""
    from scenografia import web

    assert hasattr(web, "render_sidebar_settings")
    assert hasattr(web, "render_text_mode_inputs")
    assert hasattr(web, "display_generation_results")
    assert hasattr(web, "on_regenerate")


@patch("streamlit.checkbox")
@patch("streamlit.sidebar")
@patch("streamlit.selectbox")
@patch("streamlit.text_area")
@patch("streamlit.expander")
@patch("streamlit.header")
def test_render_sidebar_settings(mock_header, mock_expander, mock_text_area, mock_selectbox, mock_sidebar, mock_checkbox):
    """Test sidebar component rendering and configuration extraction."""
    from scenografia.web.sidebar import render_sidebar_settings

    mock_checkbox.return_value = True
    # Provide return values for selectbox calls: mode, orientation, style, division, layer
    mock_selectbox.side_effect = ["standard", "landscape", "Default", "Nessuna", "background"]

    cfg = render_sidebar_settings(["Default", "Minimal"])
    assert cfg["mode"] == "standard"
    assert cfg["orientation"] == "landscape"
    assert cfg["selected_style_name"] == "Default"
    assert cfg["division"] == "Nessuna"
    assert cfg["layer"] == "background"
    assert cfg["export_svg"] is True
    assert cfg["model_override"] is None


@patch("streamlit.columns")
@patch("streamlit.button")
@patch("streamlit.text_area")
@patch("streamlit.file_uploader")
@patch("streamlit.checkbox")
@patch("streamlit.expander")
@patch("streamlit.subheader")
def test_render_text_mode_inputs(
    mock_subheader,
    mock_expander,
    mock_checkbox,
    mock_uploader,
    mock_text_area,
    mock_button,
    mock_columns,
):
    """Test text mode inputs component rendering and state return."""
    mock_state = MockSessionState({"prompt_val": "A mystical forest", "enhanced_prompt": None})
    with patch("streamlit.session_state", mock_state):
        from scenografia.web.prompt_editor import render_text_mode_inputs

        col1 = MagicMock()
        col2 = MagicMock()
        mock_columns.return_value = [col1, col2]
        mock_text_area.return_value = "A mystical forest"
        mock_uploader.return_value = None
        mock_checkbox.side_effect = [True, True]
        mock_button.return_value = False

        result = render_text_mode_inputs(division="Nessuna", selected_style_name="Default")
        assert result["generate_clicked"] is False
        assert result["prompt"] == "A mystical forest"
        assert result["ref_image_bytes"] is None
        assert result["use_as_layout"] is True


def test_on_regenerate_text(tmp_path):
    """Test on_regenerate callback for text generation."""
    mock_state = MockSessionState({"select_mode": "standard", "prompt_add": "more lights"})
    with patch("streamlit.session_state", mock_state):
        with patch("scenografia.services.text_generation_service.TextGenerationService.run_text_generation") as mock_run_text:
            from scenografia.web.results_view import on_regenerate

            test_img = tmp_path / "final.png"
            test_img.write_bytes(b"\x89PNG\r\n\x1a\n")

            mock_run_text.return_value = {
                "output_dir": tmp_path,
                "image_path": test_img,
                "prompt_path": tmp_path / "prompt.txt",
            }

            on_regenerate(
                output_dir=tmp_path,
                image_path_obj=test_img,
                sketch_path=None,
                original_prompt="A stone portal",
                orientation_val="landscape",
                input_type="text",
                selected_style="Default",
                new_mode_key="select_mode",
                additions_key="prompt_add",
            )

            mock_run_text.assert_called_once()
            assert "more lights" in mock_run_text.call_args.kwargs["prompt"]
