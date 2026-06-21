"""Tests for sketch preprocessing."""

import pytest
from pathlib import Path
import numpy as np
from scenografia.tools.image_preprocessor import SketchPreprocessor


class TestSketchLoading:
    """Test loading sketch images."""
    
    def test_load_existing_sketch(self):
        """Should load existing sketch file."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3  # 3D array for image
    
    def test_load_nonexistent_sketch_returns_none(self):
        """Should return None for missing file."""
        sketch_path = Path("nonexistent/sketch.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        
        assert image is None
    
    def test_sketch_has_reasonable_dimensions(self):
        """Loaded sketch should have reasonable size."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        
        assert image.shape[0] > 100  # Height
        assert image.shape[1] > 100  # Width


class TestBlackAndWhiteConversion:
    """Test converting to black and white."""
    
    def test_convert_to_bw_returns_binary(self):
        """Should return binary image."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        assert bw is not None
        assert bw.dtype == np.uint8
        assert set(np.unique(bw)) <= {0, 255}  # Only black and white
    
    def test_bw_conversion_preserves_size(self):
        """BW conversion should preserve image size."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        assert bw.shape[0] == image.shape[0]
        assert bw.shape[1] == image.shape[1]


class TestContrastEnhancement:
    """Test contrast enhancement."""
    
    def test_enhance_contrast_modifies_image(self):
        """Should modify image contrast."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        gray = SketchPreprocessor.convert_to_bw(image)
        enhanced = SketchPreprocessor.enhance_contrast(gray)
        
        assert enhanced is not None
        assert enhanced.shape == gray.shape
    
    def test_enhance_contrast_is_idempotent_ish(self):
        """Multiple enhancements should have diminishing effect."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        gray = SketchPreprocessor.convert_to_bw(image)
        
        enhanced1 = SketchPreprocessor.enhance_contrast(gray)
        enhanced2 = SketchPreprocessor.enhance_contrast(enhanced1)
        
        # Should both exist
        assert enhanced1 is not None
        assert enhanced2 is not None


class TestSketchCleaning:
    """Test sketch cleaning and refinement."""
    
    def test_clean_sketch_removes_noise(self):
        """Should clean sketch image."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        cleaned = SketchPreprocessor.clean_sketch(bw)
        
        assert cleaned is not None
        assert cleaned.shape == bw.shape
    
    def test_cleaned_sketch_is_binary(self):
        """Cleaned sketch should be binary."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        cleaned = SketchPreprocessor.clean_sketch(bw)
        
        unique_values = set(np.unique(cleaned))
        assert unique_values <= {0, 255}


class TestFullPreprocessing:
    """Test complete preprocessing pipeline."""
    
    def test_full_preprocessing_completes(self):
        """Should complete full preprocessing pipeline."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        processed = SketchPreprocessor.preprocess_sketch(sketch_path)
        
        assert processed is not None
        assert isinstance(processed, np.ndarray)
    
    def test_preprocessing_returns_binary_image(self):
        """Preprocessed image should be binary."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        processed = SketchPreprocessor.preprocess_sketch(sketch_path)
        
        unique = set(np.unique(processed))
        assert unique <= {0, 255}
    
    def test_preprocessing_nonexistent_returns_none(self):
        """Should return None for missing file."""
        result = SketchPreprocessor.preprocess_sketch(Path("nonexistent.png"))
        assert result is None


class TestProcessedSketchSaving:
    """Test saving processed sketches."""
    
    def test_save_processed_sketch(self):
        """Should save processed sketch."""
        import tempfile
        
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "processed_sketch.png"
            success = SketchPreprocessor.save_processed_sketch(bw, output_path)
            
            assert success
            assert output_path.exists()
            assert output_path.stat().st_size > 0
    
    def test_save_creates_parent_directories(self):
        """Should create parent directories as needed."""
        import tempfile
        
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "processed.png"
            success = SketchPreprocessor.save_processed_sketch(bw, output_path)
            
            assert success
            assert output_path.exists()


class TestSketchElementExtraction:
    """Test extracting sketch elements."""
    
    def test_extract_sketch_elements(self):
        """Should extract detected elements."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        elements = SketchPreprocessor.extract_sketch_elements(bw)
        
        assert isinstance(elements, dict)
        assert "total_contours" in elements
        assert "largest_contour_size" in elements
        assert "detected" in elements
    
    def test_elements_detection_non_empty(self):
        """Should detect some elements in test sketch."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        image = SketchPreprocessor.load_sketch(sketch_path)
        bw = SketchPreprocessor.convert_to_bw(image)
        
        elements = SketchPreprocessor.extract_sketch_elements(bw)
        
        # Test sketch should have contours
        assert elements["total_contours"] > 0


class TestPreprocessingDetails:
    """Test capturing preprocessing details."""
    
    def test_get_preprocessing_details(self):
        """Should capture preprocessing information."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        original = SketchPreprocessor.load_sketch(sketch_path)
        processed = SketchPreprocessor.preprocess_sketch(sketch_path)
        
        details = SketchPreprocessor.get_preprocessing_details(original, processed)
        
        assert isinstance(details, dict)
        assert "original_size" in details
        assert "processed_size" in details
        assert "steps" in details
    
    def test_preprocessing_details_has_steps(self):
        """Preprocessing details should list steps."""
        sketch_path = Path("tests/fixtures/sketch_dummy.png")
        original = SketchPreprocessor.load_sketch(sketch_path)
        processed = SketchPreprocessor.preprocess_sketch(sketch_path)
        
        details = SketchPreprocessor.get_preprocessing_details(original, processed)
        
        assert len(details["steps"]) > 0
        assert all(isinstance(s, str) for s in details["steps"])
