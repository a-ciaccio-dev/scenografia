"""Tests for scenic depth layering in SVG Vectorizer and OutputManager."""

from pathlib import Path
from PIL import Image, ImageDraw
import pytest

from scenografia.tools.svg_vectorizer import SvgVectorizer
from scenografia.tools.output_manager import OutputManager


@pytest.fixture
def test_image(tmp_path):
    img_path = tmp_path / "layer_test.png"
    img = Image.new("RGB", (150, 100), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 120, 80], fill=(220, 180, 50))
    img.save(img_path)
    return img_path


def test_svg_vectorizer_injects_layer_group_tag(test_image, tmp_path):
    """Verify that SvgVectorizer injects semantic <g id='scenic-layer-...'> groups."""
    vectorizer = SvgVectorizer()
    out_svg = tmp_path / "foreground.svg"

    result = vectorizer.vectorize_image(
        test_image,
        output_svg_path=out_svg,
        mode="color",
        layer="foreground",
    )

    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert '<g id="scenic-layer-foreground" data-layer="foreground">' in content
    assert "</g>" in content


def test_svg_vectorizer_monochrome_injects_layer_group_tag(test_image, tmp_path):
    """Verify that monochrome vectorizer also injects semantic <g id='scenic-layer-...'>."""
    vectorizer = SvgVectorizer()
    out_svg = tmp_path / "background_bw.svg"

    result = vectorizer.vectorize_image(
        test_image,
        output_svg_path=out_svg,
        mode="monochrome",
        layer="background",
    )

    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert '<g id="scenic-layer-background" data-layer="background">' in content
    assert "</g>" in content


def test_output_manager_save_svg_propagates_layer(test_image, tmp_path):
    """Verify OutputManager.save_svg passes layer to SvgVectorizer."""
    out_dir = tmp_path / "run_dir"
    out_dir.mkdir()

    svg_file = OutputManager.save_svg(
        output_dir=out_dir,
        image_path=test_image,
        mode="color",
        layer="midground",
    )

    assert svg_file.exists()
    content = svg_file.read_text(encoding="utf-8")
    assert '<g id="scenic-layer-midground" data-layer="midground">' in content
