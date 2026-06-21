"""Tests for configuration loading and mode-to-model mapping."""

import pytest
from pathlib import Path
from scenografia.config import Config
from scenografia.schemas.generation_schema import GenerationMode
import os


class TestConfigInitialization:
    """Test configuration initialization."""
    
    def test_config_requires_api_key(self):
        """API key should be required."""
        # Save original
        original_key = os.getenv("OPENROUTER_API_KEY")
        try:
            # Clear the key
            if "OPENROUTER_API_KEY" in os.environ:
                del os.environ["OPENROUTER_API_KEY"]
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                Config.OPENROUTER_API_KEY = None
                Config.validate()
        finally:
            # Restore
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key
    
    def test_config_default_values(self):
        """Test default configuration values."""
        assert Config.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
        assert Config.APP_INPUT_DIR == "input"
        assert Config.APP_OUTPUT_DIR == "output"
        assert Config.APP_DEBUG == False


class TestModelMapping:
    """Test mode-to-model mapping functionality."""
    
    def test_get_model_for_mode_returns_none_when_not_configured(self):
        """Should return None for unconfigured mode."""
        # Clear environment
        for mode in ["DRAFT", "STANDARD", "PRODUCTION", "VECTOR_READY"]:
            env_var = f"OPENROUTER_{mode}_MODEL"
            if env_var in os.environ:
                del os.environ[env_var]
        
        Config._initialize_model_mapping()
        result = Config.get_model_for_mode(GenerationMode.DRAFT)
        assert result is None
    
    def test_get_model_id_with_override(self):
        """Override should take precedence."""
        override_model = "custom-model-123"
        result = Config.get_model_id(GenerationMode.STANDARD, override_model)
        assert result == override_model
    
    def test_get_model_id_fallback_default(self):
        """Should use fallback default when no override or config."""
        # Clear environment
        for mode in ["DRAFT", "STANDARD", "PRODUCTION", "VECTOR_READY"]:
            env_var = f"OPENROUTER_{mode}_MODEL"
            if env_var in os.environ:
                del os.environ[env_var]
        
        Config._initialize_model_mapping()
        result = Config.get_model_id(GenerationMode.STANDARD, None)
        assert result is not None
        assert isinstance(result, str)


class TestConfigDirectories:
    """Test directory configuration."""
    
    def test_config_creates_output_directory(self):
        """Config.validate() should create output directory."""
        # Ensure API key is set
        os.environ["OPENROUTER_API_KEY"] = "test-key"
        Config.initialize()  # Reload config with new API key
        
        # Create a temporary output dir for testing
        test_output = Path("test_output_config")
        original_output = Config.APP_OUTPUT_DIR
        
        try:
            Config.APP_OUTPUT_DIR = str(test_output)
            Config.validate()
            assert test_output.exists()
        finally:
            # Cleanup
            if test_output.exists():
                import shutil
                shutil.rmtree(test_output)
            Config.APP_OUTPUT_DIR = original_output
    
    def test_config_validate_returns_true(self):
        """Config.validate() should return True when valid."""
        # Ensure API key is set
        os.environ["OPENROUTER_API_KEY"] = "test-key"
        Config.initialize()  # Reload config with new API key
        result = Config.validate()
        assert result is True
