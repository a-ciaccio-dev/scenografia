"""Unit and integration tests for CLI command 'scenografia vectorize'."""

from pathlib import Path
from typer.testing import CliRunner
from PIL import Image, ImageDraw
import pytest

from scenografia.main import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "portal_scene.png"
    img = Image.new("RGB", (200, 120), color=(30, 40, 80))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 30, 160, 90], fill=(220, 190, 70))
    img.save(img_path)
    return img_path


def test_vectorize_cli_missing_image(runner):
    """Should exit with code 2 when input image file does not exist."""
    result = runner.invoke(app, ["vectorize", "non_existing_scene.png"])
    assert result.exit_code == 2
    assert "Error: image not found" in result.output


def test_vectorize_cli_success_with_options(runner, sample_image, tmp_path):
    """Should vectorize image with explicit output, mode, and layer options."""
    out_svg = tmp_path / "custom_vector.svg"
    result = runner.invoke(
        app,
        [
            "vectorize",
            str(sample_image),
            "--output",
            str(out_svg),
            "--mode",
            "color",
            "--layer",
            "foreground",
            "--max-colors",
            "8",
        ],
    )

    assert result.exit_code == 0
    assert "Vector SVG saved to" in result.output
    assert out_svg.exists()

    content = out_svg.read_text(encoding="utf-8")
    assert "<svg" in content
    assert '<g id="scenic-layer-foreground" data-layer="foreground">' in content


def test_vectorize_cli_monochrome(runner, sample_image):
    """Should vectorize image in monochrome mode using default output path."""
    result = runner.invoke(
        app,
        [
            "vectorize",
            str(sample_image),
            "--mode",
            "monochrome",
            "--layer",
            "background",
        ],
    )

    expected_svg = sample_image.with_suffix(".svg")
    assert result.exit_code == 0
    assert expected_svg.exists()

    content = expected_svg.read_text(encoding="utf-8")
    assert '<g id="scenic-layer-background" data-layer="background">' in content
