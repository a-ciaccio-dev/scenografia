"""
Image preprocessing utilities for sketch handling.

Provides local black-and-white sketch preprocessing and optional
AI-assisted refinement capabilities.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
from PIL import Image, ImageEnhance


class SketchPreprocessor:
    """Handles sketch preprocessing and enhancement."""
    
    @staticmethod
    def load_sketch(sketch_path: Path) -> Optional[np.ndarray]:
        """
        Load a sketch image.
        
        Args:
            sketch_path: Path to sketch image
            
        Returns:
            Image array or None if load fails
        """
        try:
            if not sketch_path.exists():
                return None
            
            # Load with OpenCV (BGR)
            image = cv2.imread(str(sketch_path))
            if image is None:
                return None
            
            return image
        except Exception:
            return None
    
    @staticmethod
    def convert_to_bw(image: np.ndarray) -> np.ndarray:
        """
        Convert image to black and white.
        
        Args:
            image: Input image array (BGR or RGB)
            
        Returns:
            Black and white image array
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold to get binary image
        bw = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        return bw
    
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance contrast of sketch.
        
        Args:
            image: Input image array
            
        Returns:
            Enhanced image array
        """
        # Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        return enhanced
    
    @staticmethod
    def clean_sketch(image: np.ndarray) -> np.ndarray:
        """
        Clean and refine sketch using morphological operations.
        
        Args:
            image: Input binary image
            
        Returns:
            Cleaned image array
        """
        # Create kernel for morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        # Remove small noise
        cleaned = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return cleaned
    
    @staticmethod
    def preprocess_sketch(sketch_path: Path) -> Optional[np.ndarray]:
        """
        Fully preprocess a sketch image.
        
        Steps:
        1. Load image
        2. Convert to black and white
        3. Enhance contrast
        4. Clean with morphological ops
        
        Args:
            sketch_path: Path to sketch file
            
        Returns:
            Preprocessed image array or None
        """
        image = SketchPreprocessor.load_sketch(sketch_path)
        if image is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        enhanced = SketchPreprocessor.enhance_contrast(gray)
        
        # Convert to binary
        bw = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Clean
        cleaned = SketchPreprocessor.clean_sketch(bw)
        
        return cleaned
    
    @staticmethod
    def save_processed_sketch(
        processed_image: np.ndarray,
        output_path: Path
    ) -> bool:
        """
        Save processed sketch image.
        
        Args:
            processed_image: Processed image array
            output_path: Where to save
            
        Returns:
            True if successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), processed_image)
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract_sketch_elements(image: np.ndarray) -> Dict[str, Any]:
        """
        Extract detected elements from sketch for description.
        
        Args:
            image: Processed sketch image
            
        Returns:
            Dictionary with detected elements
        """
        # Find contours
        contours, _ = cv2.findContours(
            image,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        elements = {
            "total_contours": len(contours),
            "largest_contour_size": max(
                [cv2.contourArea(c) for c in contours]
            ) if contours else 0,
            "image_size": image.shape,
            "detected": []
        }
        
        # Classify contours by size
        if contours:
            total_area = image.size
            for i, contour in enumerate(sorted(contours, key=cv2.contourArea, reverse=True)[:10]):
                area = cv2.contourArea(contour)
                if area > total_area * 0.01:  # Significant contour
                    elements["detected"].append({
                        "size": float(area),
                        "perimeter": float(cv2.arcLength(contour, True))
                    })
        
        return elements
    
    @staticmethod
    def get_preprocessing_details(
        original_image: np.ndarray,
        processed_image: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get details about preprocessing that was applied.
        
        Args:
            original_image: Original image
            processed_image: Processed image
            
        Returns:
            Dictionary with preprocessing details
        """
        return {
            "original_size": [int(original_image.shape[1]), int(original_image.shape[0])],
            "processed_size": [int(processed_image.shape[1]), int(processed_image.shape[0])],
            "contrast_adjusted": True,
            "morphological_ops": True,
            "binary_conversion": True,
            "steps": [
                "Load image",
                "Convert to grayscale",
                "Enhance contrast",
                "Adaptive threshold",
                "Morphological cleaning"
            ]
        }
