"""
SVG Vectorizer tool for theatrical scenic designs.
Converts raster images (PNG, JPEG) into scalable vector graphics (SVG)
using OpenCV contour extraction and polygon approximation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from scenografia.logger import setup_logger

logger = setup_logger("svg_vectorizer")


class SvgVectorizer:
    """
    Converts raster scenic designs into scalable vector SVG documents.
    Supports monochrome line-art vectorization and multi-color layered vectorization.
    """

    def __init__(
        self,
        epsilon_factor: float = 0.0015,
        min_contour_area: float = 8.0,
        max_colors: int = 12,
    ) -> None:
        """
        Initialize the vectorizer with approximation and filtering parameters.

        Args:
            epsilon_factor: Approximation accuracy for cv2.approxPolyDP (fraction of arc length).
            min_contour_area: Minimum contour area in pixels to retain (filters out tiny noise).
            max_colors: Number of color clusters for color quantization.
        """
        self.epsilon_factor = epsilon_factor
        self.min_contour_area = min_contour_area
        self.max_colors = max_colors

    def vectorize_image(
        self,
        image_path: Path | str,
        output_svg_path: Optional[Path | str] = None,
        mode: str = "color",
    ) -> Path:
        """
        Vectorize an image file and save as an SVG document.

        Args:
            image_path: Path to the input raster image.
            output_svg_path: Optional output path. Defaults to same name with .svg extension.
            mode: Vectorization mode ("color", "monochrome", or "lineart").

        Returns:
            Path to the generated .svg file.
        """
        in_path = Path(image_path)
        if not in_path.exists():
            raise FileNotFoundError(f"Input image not found: {in_path}")

        if output_svg_path is None:
            out_path = in_path.with_suffix(".svg")
        else:
            out_path = Path(output_svg_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Avvio vettorizzazione di '{in_path}' in modalità '{mode}'...")

        # Read image
        img = cv2.imread(str(in_path))
        if img is None:
            # Fallback to PIL in case of Unicode path issues on Windows
            pil_img = Image.open(in_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        height, width = img.shape[:2]

        if mode in ("monochrome", "lineart", "bw"):
            svg_content = self._vectorize_monochrome(img, width, height)
        else:
            svg_content = self._vectorize_color(img, width, height)

        out_path.write_text(svg_content, encoding="utf-8")
        logger.info(f"Vettorizzazione completata. SVG salvato in: {out_path} ({len(svg_content)} bytes)")
        return out_path

    def _contour_to_svg_path(self, contour: np.ndarray) -> str:
        """Convert an OpenCV contour into an SVG path 'd' string."""
        if len(contour) < 3:
            return ""

        # Approximate polygon to reduce node count and create smooth vector lines
        epsilon = self.epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < 3:
            approx = contour

        pts = approx.reshape(-1, 2)
        start_x, start_y = pts[0]
        commands = [f"M {start_x} {start_y}"]
        for x, y in pts[1:]:
            commands.append(f"L {x} {y}")
        commands.append("Z")
        return " ".join(commands)

    def _vectorize_monochrome(self, img: np.ndarray, width: int, height: int) -> str:
        """Vectorize image as high-contrast monochrome line-art."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Adaptive or Otsu threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        svg_paths: list[str] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self.min_contour_area:
                d = self._contour_to_svg_path(cnt)
                if d:
                    svg_paths.append(f'  <path d="{d}" fill="#111111" stroke="none" />')

        paths_str = "\n".join(svg_paths)
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
            f'  <rect width="100%" height="100%" fill="#ffffff" />\n'
            f'{paths_str}\n'
            f'</svg>'
        )

    def _vectorize_color(self, img: np.ndarray, width: int, height: int) -> str:
        """Vectorize image using K-Means color quantization and multi-layer contouring."""
        # Reshape image pixels for k-means
        data = img.reshape((-1, 3)).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        # Fast vectorized 24-bit color packing to determine exact unique RGB color count
        packed_colors = (
            img[:, :, 0].astype(np.int32)
            + (img[:, :, 1].astype(np.int32) << 8)
            + (img[:, :, 2].astype(np.int32) << 16)
        )
        unique_color_count = len(np.unique(packed_colors))
        k = max(2, min(self.max_colors, unique_color_count))
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

        centers = np.uint8(centers)
        labels = labels.flatten()

        # Sort color clusters by luminance (draw darker shapes over lighter or vice versa)
        def luminance(bgr):
            return 0.299 * bgr[2] + 0.587 * bgr[1] + 0.114 * bgr[0]

        cluster_order = sorted(range(k), key=lambda idx: luminance(centers[idx]), reverse=True)

        svg_elements: list[str] = []

        # Background color: use the most dominant cluster
        counts = np.bincount(labels, minlength=k)
        dom_idx = int(np.argmax(counts))
        dom_bgr = centers[dom_idx]
        dom_hex = f"#{dom_bgr[2]:02x}{dom_bgr[1]:02x}{dom_bgr[0]:02x}"
        svg_elements.append(f'  <rect width="100%" height="100%" fill="{dom_hex}" />')

        # Generate paths for each non-dominant cluster
        for idx in cluster_order:
            if idx == dom_idx:
                continue

            mask = (labels == idx).reshape((height, width)).astype(np.uint8) * 255
            # Morphological smoothing to eliminate speckles
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            bgr = centers[idx]
            hex_color = f"#{bgr[2]:02x}{bgr[1]:02x}{bgr[0]:02x}"

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area >= self.min_contour_area:
                    d = self._contour_to_svg_path(cnt)
                    if d:
                        svg_elements.append(f'  <path d="{d}" fill="{hex_color}" stroke="none" />')

        elements_str = "\n".join(svg_elements)
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
            f'{elements_str}\n'
            f'</svg>'
        )
