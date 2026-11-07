"""
Antigravity Bridge Provider.

Enables image and text generation within the Antigravity agentic workspace,
supporting file-based bridge exchange and local fallback generation.
"""

import os
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw
import io

from scenografia.schemas.generation_schema import Orientation, ImageGenerationResponse
from scenografia.providers.base import BaseImageProvider, BaseTextProvider


class AntigravityBridgeProvider(BaseImageProvider, BaseTextProvider):
    """
    Provider that bridges Scenografia to Antigravity subagents or workspace files.
    Allows running pipelines offline or natively through Antigravity agent tools.
    """

    def __init__(self, bridge_dir: str = "output/antigravity_bridge"):
        self.bridge_dir = Path(bridge_dir)
        self.bridge_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: Optional[str] = None,
        orientation: Orientation = Orientation.LANDSCAPE,
        input_image_bytes: Optional[bytes] = None,
    ) -> ImageGenerationResponse:
        """
        Produce a scenic design image via Antigravity bridge.
        If an external file is waiting in the bridge dir, it uses it;
        otherwise generates a stylized SVG-ready theatrical canvas.
        """
        # Determine aspect ratio resolution
        if orientation == Orientation.LANDSCAPE:
            width, height = 1280, 720
        elif orientation == Orientation.PORTRAIT:
            width, height = 720, 1280
        else:
            width, height = 1024, 1024

        # Check for pre-rendered image in bridge dir
        bridge_image = self.bridge_dir / "latest_subagent_output.png"
        if bridge_image.exists():
            image_data = bridge_image.read_bytes()
        else:
            # Generate a theatrical scenic base canvas with flat color blocks
            img = Image.new("RGBA", (width, height), color=(240, 235, 220, 255))
            draw = ImageDraw.Draw(img)

            # Sky / Backdrop fill
            sky_height = int(height * 0.65)
            draw.rectangle([0, 0, width, sky_height], fill=(135, 175, 205, 255))

            # Horizon / Mountains / Scenic Backdrop
            draw.polygon([
                (0, sky_height),
                (int(width * 0.25), int(sky_height * 0.6)),
                (int(width * 0.5), sky_height),
                (int(width * 0.75), int(sky_height * 0.5)),
                (width, sky_height)
            ], fill=(80, 110, 140, 255), outline=(30, 45, 60, 255), width=3)

            # Ground / Stage level
            draw.rectangle([0, sky_height, width, height], fill=(180, 150, 110, 255), outline=(40, 30, 20, 255), width=4)

            # Side wings (Quinte sceniche)
            wing_width = int(width * 0.15)
            draw.rectangle([0, int(height * 0.2), wing_width, height], fill=(70, 50, 40, 255), outline=(20, 15, 10, 255), width=4)
            draw.rectangle([width - wing_width, int(height * 0.2), width, height], fill=(70, 50, 40, 255), outline=(20, 15, 10, 255), width=4)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            image_data = buffer.getvalue()

        return ImageGenerationResponse(
            image_data=image_data,
            model_used=model_id or "antigravity/native-image-generator",
            request_id=f"ag_{os.urandom(4).hex()}",
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """Generate structured theatrical prompt specification natively."""
        scene_name = prompt.strip().upper()[:30]
        return (
            f"🎨 DATI TECNICI – FONDALE TEATRALE: {scene_name}\n\n"
            f"📐 COMPOSIZIONE E PROSPETTIVA:\n"
            f"- Disposizione frontale ad arco di proscenio con visione teatrale pulita.\n"
            f"- Proporzioni panoramiche 16:9 con profondità a piani scenici ben distinti.\n\n"
            f"🧱 ELEMENTI SCENOGRAFICI PRINCIPALI:\n"
            f"- {prompt.strip()}\n"
            f"- Contorni netti a tratto chiuso, adatti a conversione vettoriale SVG.\n\n"
            f"🎨 PALETTE COLORI E ILLUMINAZIONE:\n"
            f"- Colori solidi e campiture piatte, assenza di gradienti complessi e sfumature digitali.\n"
        )
