"""
Unit tests for history gallery component (scenografia.web.history_gallery).
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scenografia.web.history_gallery import render_history_gallery


class MockSessionState(dict):
    """Mock Streamlit session_state supporting both attribute and dict syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


@patch("streamlit.info")
@patch("streamlit.subheader")
@patch("streamlit.divider")
def test_render_history_gallery_empty(mock_divider, mock_subheader, mock_info, tmp_path):
    """Should show info message if no runs exist in output directory."""
    render_history_gallery(output_dir=tmp_path)
    mock_info.assert_called_once_with("Nessun run trovato ancora.")


@patch("streamlit.rerun")
@patch("streamlit.download_button")
@patch("streamlit.button")
@patch("streamlit.container")
@patch("streamlit.columns")
@patch("streamlit.selectbox")
@patch("streamlit.caption")
@patch("streamlit.markdown")
@patch("streamlit.image")
@patch("streamlit.subheader")
@patch("streamlit.divider")
def test_render_history_gallery_with_runs(
    mock_divider,
    mock_subheader,
    mock_image,
    mock_markdown,
    mock_caption,
    mock_selectbox,
    mock_columns,
    mock_container,
    mock_button,
    mock_download,
    mock_rerun,
    tmp_path,
):
    """Should render runs with filters and metadata."""
    # Create a mock run directory structure
    run_dir = tmp_path / "2026-06-25_1200_run-001"
    run_dir.mkdir(parents=True)
    img_file = run_dir / "final.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    meta_file = run_dir / "generation_response.json"
    meta_file.write_text(json.dumps({"style_name": "Minimalist"}), encoding="utf-8")

    report_file = run_dir / "validation_report.json"
    report_file.write_text(
        json.dumps({
            "orientation_valid": True,
            "style_contract_applied": True,
            "orientation": "landscape",
        }),
        encoding="utf-8",
    )

    # Filter selects return "Tutti"
    mock_selectbox.side_effect = ["Tutti", "Tutti"]
    mock_columns.side_effect = lambda n: [MagicMock() for _ in (range(n) if isinstance(n, int) else range(len(n)))]
    mock_button.return_value = False

    mock_state = MockSessionState()
    with patch("streamlit.session_state", mock_state):
        render_history_gallery(output_dir=tmp_path)

        mock_image.assert_called_once()
        assert any("Minimalist" in str(c) for c in mock_caption.call_args_list)
