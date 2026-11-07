"""
Antigravity Bridge Provider.

Enables image and text generation within the Antigravity agentic workspace,
supporting file-based bridge exchange, subagent orchestration, and native fallback generation.
"""

import os
import json
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
        # Save request metadata for subagent inspection/handshake
        req_meta = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model_id": model_id,
            "orientation": orientation.value if hasattr(orientation, "value") else str(orientation),
            "has_input_image": input_image_bytes is not None,
        }
        try:
            (self.bridge_dir / "latest_request.json").write_text(json.dumps(req_meta, indent=2), encoding="utf-8")
        except Exception:
            pass

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
        elif input_image_bytes:
            # Image-to-image mode: use the input image as base and enhance it
            try:
                with Image.open(io.BytesIO(input_image_bytes)) as pil_img:
                    resized = pil_img.convert("RGBA").resize((width, height))
                    draw = ImageDraw.Draw(resized)
                    # Accentuate stage lighting and contours
                    draw.rectangle([10, 10, width - 10, height - 10], outline=(255, 215, 0, 180), width=4)
                    buf = io.BytesIO()
                    resized.save(buf, format="PNG")
                    image_data = buf.getvalue()
            except Exception:
                image_data = input_image_bytes
        else:
            # Detect layer isolation from prompt
            prompt_lower = prompt.lower()
            layer = "all"
            if "depth layer isolation: foreground" in prompt_lower or "layer: foreground" in prompt_lower:
                layer = "foreground"
            elif "depth layer isolation: midground" in prompt_lower or "layer: midground" in prompt_lower:
                layer = "midground"
            elif "depth layer isolation: background" in prompt_lower or "layer: background" in prompt_lower:
                layer = "background"

            # Generate a theatrical scenic base canvas with flat color blocks
            img = Image.new("RGBA", (width, height), color=(240, 235, 220, 255))
            draw = ImageDraw.Draw(img)

            sky_height = int(height * 0.65)

            # 1. Background layer
            if layer in ("all", "background"):
                # Sky / Backdrop fill
                draw.rectangle([0, 0, width, sky_height], fill=(135, 175, 205, 255))
                # Horizon / Mountains / Scenic Backdrop
                draw.polygon([
                    (0, sky_height),
                    (int(width * 0.25), int(sky_height * 0.6)),
                    (int(width * 0.5), sky_height),
                    (int(width * 0.75), int(sky_height * 0.5)),
                    (width, sky_height)
                ], fill=(80, 110, 140, 255), outline=(30, 45, 60, 255), width=3)

            # Ground / Stage level (common anchor)
            draw.rectangle([0, sky_height, width, height], fill=(180, 150, 110, 255), outline=(40, 30, 20, 255), width=4)

            # 2. Midground layer
            if layer in ("all", "midground"):
                # Middle practical architectural element (central arch/platform)
                platform_w = int(width * 0.4)
                p_left = int(width * 0.3)
                p_top = int(sky_height * 0.75)
                draw.rectangle([p_left, p_top, p_left + platform_w, sky_height + int(height * 0.1)], fill=(120, 130, 140, 255), outline=(30, 40, 50, 255), width=3)
                # Semicircular arch cutout/platform
                draw.arc([p_left + int(platform_w * 0.2), p_top - 30, p_left + int(platform_w * 0.8), p_top + 50], start=180, end=360, fill=(40, 50, 60, 255), width=4)

            # 3. Foreground layer
            if layer in ("all", "foreground"):
                # Side wings (Quinte sceniche)
                wing_width = int(width * 0.15)
                draw.rectangle([0, int(height * 0.15), wing_width, height], fill=(70, 50, 40, 255), outline=(20, 15, 10, 255), width=4)
                draw.rectangle([width - wing_width, int(height * 0.15), width, height], fill=(70, 50, 40, 255), outline=(20, 15, 10, 255), width=4)
                # Upper theatrical valance / border (soffitto scenico)
                draw.rectangle([0, 0, width, int(height * 0.12)], fill=(60, 40, 30, 255), outline=(20, 15, 10, 255), width=3)

            # Scenic division vertical dividers
            if "divided into 2" in prompt_lower or "2 parti" in prompt_lower:
                col_w = int(width * 0.04)
                mid_x = width // 2
                draw.rectangle([mid_x - col_w // 2, 0, mid_x + col_w // 2, height], fill=(95, 75, 60, 255), outline=(30, 20, 15, 255), width=3)
            elif "divided into 3" in prompt_lower or "3 parti" in prompt_lower:
                col_w = int(width * 0.03)
                for step in (1, 2):
                    col_x = (width * step) // 3
                    draw.rectangle([col_x - col_w // 2, 0, col_x + col_w // 2, height], fill=(95, 75, 60, 255), outline=(30, 20, 15, 255), width=3)
            elif "divided into 4" in prompt_lower or "4 parti" in prompt_lower:
                col_w = int(width * 0.025)
                for step in (1, 2, 3):
                    col_x = (width * step) // 4
                    draw.rectangle([col_x - col_w // 2, 0, col_x + col_w // 2, height], fill=(95, 75, 60, 255), outline=(30, 20, 15, 255), width=3)

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
        layer_note = ""
        combined_text = f"{prompt} {system_instruction or ''}".lower()
        if "foreground" in combined_text or "primo piano" in combined_text:
            layer_note = "\n- Isolamento piano di profondità: PRIMO PIANO (Quinte, cieli e proscenio)."
        elif "midground" in combined_text or "mezzo piano" in combined_text:
            layer_note = "\n- Isolamento piano di profondità: MEZZO PIANO (Praticabili, architetture e strutture mediane)."
        elif "background" in combined_text or "fondale" in combined_text:
            layer_note = "\n- Isolamento piano di profondità: FONDALE (Backdrop, orizzonte e cielo)."

        division_note = ""
        if "2 parti" in combined_text or "divided into 2" in combined_text:
            division_note = "\n- Suddivisione scenica: 2 sezioni simmetriche separate da elemento verticale centrale."
        elif "3 parti" in combined_text or "divided into 3" in combined_text:
            division_note = "\n- Suddivisione scenica: 3 pannelli verticali uguali separati da colonne o quinte."
        elif "4 parti" in combined_text or "divided into 4" in combined_text:
            division_note = "\n- Suddivisione scenica: 4 pannelli verticali con ritmo modulare."

        return (
            f"🎨 DATI TECNICI – FONDALE TEATRALE: {scene_name}\n\n"
            f"📐 COMPOSIZIONE E PROSPETTIVA:\n"
            f"- Disposizione frontale ad arco di proscenio con visione teatrale pulita.{division_note}{layer_note}\n"
            f"- Proporzioni panoramiche con profondità a piani scenici ben distinti.\n\n"
            f"🧱 ELEMENTI SCENOGRAFICI PRINCIPALI:\n"
            f"- {prompt.strip()}\n"
            f"- Contorni netti a tratto chiuso, adatti a conversione vettoriale SVG.\n\n"
            f"🎨 PALETTE COLORI E ILLUMINAZIONE:\n"
            f"- Colori solidi e campiture piatte, assenza di gradienti complessi e sfumature digitali.\n"
        )
