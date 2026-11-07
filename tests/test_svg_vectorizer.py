"""
Unit tests for SvgVectorizer tool.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import pytest

from scenografia.tools.svg_vectorizer import SvgVectorizer


@pytest.fixture
def sample_raster_image(tmp_path) -> Path:
    """Generate a simple geometric test PNG image."""
    img_path = tmp_path / "test_scene.png"
    img = Image.new("RGB", (200, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw a blue rectangle (scenic backdrop)
    draw.rectangle([20, 20, 180, 80], fill=(30, 80, 190))
    # Draw a red circle (scenic portal/element)
    draw.ellipse([70, 40, 130, 100], fill=(210, 40, 40))
    img.save(img_path)
    return img_path


def test_svg_vectorizer_missing_file():
    """Should raise FileNotFoundError when image does not exist."""
    vectorizer = SvgVectorizer()
    with pytest.raises(FileNotFoundError):
        vectorizer.vectorize_image("non_existent_file.png")


def test_svg_vectorizer_color_mode(sample_raster_image, tmp_path):
    """Should convert raster image to color SVG with paths and rect."""
    vectorizer = SvgVectorizer(min_contour_area=5.0, max_colors=4)
    out_svg = tmp_path / "output_vector.svg"

    result_path = vectorizer.vectorize_image(
        image_path=sample_raster_image,
        output_svg_path=out_svg,
        mode="color",
    )

    assert result_path.exists()
    assert result_path == out_svg

    content = result_path.read_text(encoding="utf-8")
    assert content.startswith("<?xml")
    assert "<svg" in content
    assert 'viewBox="0 0 200 150"' in content
    assert "<rect" in content
    assert "<path" in content
    assert "</svg>" in content


def test_svg_vectorizer_monochrome_mode(sample_raster_image, tmp_path):
    """Should convert raster image to high-contrast monochrome SVG."""
    vectorizer = SvgVectorizer(min_contour_area=5.0)

    result_path = vectorizer.vectorize_image(
        image_path=sample_raster_image,
        mode="monochrome",
    )

    assert result_path.exists()
    assert result_path.suffix == ".svg"
    assert result_path.stem == sample_raster_image.stem

    content = result_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert 'fill="#111111"' in content
    assert "</svg>" in content


def test_contour_to_svg_path_short_contour():
    """Should return empty string if contour points are fewer than 3."""
    vectorizer = SvgVectorizer()
    short_contour = np.array([[[10, 10]], [[20, 20]]])
    assert vectorizer._contour_to_svg_path(short_contour) == ""
