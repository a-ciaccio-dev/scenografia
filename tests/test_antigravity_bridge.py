"""Unit tests for AntigravityBridgeProvider."""

import io
from PIL import Image
from pathlib import Path
from scenografia.providers.antigravity_bridge import AntigravityBridgeProvider
from scenografia.schemas.generation_schema import Orientation


def test_antigravity_bridge_generate_layers(tmp_path):
    """Verify bridge generates images respecting depth layer prompt tags."""
    bridge = AntigravityBridgeProvider(bridge_dir=str(tmp_path))

    for layer in ("all", "background", "midground", "foreground"):
        resp = bridge.generate_image(
            prompt=f"Palazzo Reale, depth layer isolation: {layer}",
            orientation=Orientation.LANDSCAPE
        )
        assert resp.error is None
        assert resp.image_data is not None
        assert "antigravity" in resp.model_used
        with Image.open(io.BytesIO(resp.image_data)) as img:
            assert img.size == (1280, 720)


def test_antigravity_bridge_generate_divisions(tmp_path):
    """Verify bridge generates images respecting division instructions."""
    bridge = AntigravityBridgeProvider(bridge_dir=str(tmp_path))

    for div in ("2 parti", "3 parti", "4 parti"):
        resp = bridge.generate_image(
            prompt=f"Tempio greco, divisione: {div}",
            orientation=Orientation.PORTRAIT
        )
        assert resp.error is None
        with Image.open(io.BytesIO(resp.image_data)) as img:
            assert img.size == (720, 1280)


def test_antigravity_bridge_img2img(tmp_path):
    """Verify bridge supports image-to-image with input image bytes."""
    bridge = AntigravityBridgeProvider(bridge_dir=str(tmp_path))
    
    # Create a small dummy input image
    test_img = Image.new("RGBA", (200, 200), color=(100, 150, 200, 255))
    buf = io.BytesIO()
    test_img.save(buf, format="PNG")
    input_bytes = buf.getvalue()

    resp = bridge.generate_image(
        prompt="Rifinisci i dettagli architettonici",
        orientation=Orientation.SQUARE,
        input_image_bytes=input_bytes,
    )
    assert resp.error is None
    with Image.open(io.BytesIO(resp.image_data)) as img:
        assert img.size == (1024, 1024)


def test_antigravity_bridge_saves_request_metadata(tmp_path):
    """Verify bridge records request metadata in bridge_dir."""
    bridge = AntigravityBridgeProvider(bridge_dir=str(tmp_path))
    bridge.generate_image(prompt="Castello Medievale", orientation=Orientation.LANDSCAPE)

    meta_file = tmp_path / "latest_request.json"
    assert meta_file.exists()
    content = meta_file.read_text(encoding="utf-8")
    assert "Castello Medievale" in content
    assert "landscape" in content


def test_antigravity_bridge_text_generation_with_annotations(tmp_path):
    """Verify bridge text generation incorporates division and depth layers."""
    bridge = AntigravityBridgeProvider(bridge_dir=str(tmp_path))
    text = bridge.generate_text("Salone nobiliare con 3 parti e foreground")
    assert "SALONE NOBILIARE" in text
    assert "PRIMO PIANO" in text
    assert "3 pannelli" in text
