"""
Configuration loading and management for Scenografia.

Handles environment variable loading, model mapping, and configuration
validation.
"""

import os
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
from .schemas.generation_schema import GenerationMode


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try .env.local or other variants
        for variant in [".env.local", ".env.development"]:
            if Path(variant).exists():
                load_dotenv(variant)
                break


class Config:
    """Application configuration."""
    
    # Active Provider (default: antigravity native)
    SCENOGRAFIA_PROVIDER: str = "antigravity"

    # OpenRouter image generation API configuration (optional if using antigravity)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_TIMEOUT: float = 60.0
    
    # Optional enhancer model
    ANTIGRAVITY_ENHANCER_MODEL: str = "gemini-2.5-flash"
    OPENROUTER_ENHANCER_MODEL: str = "google/gemini-2.5-flash"
    
    # Application directories
    APP_INPUT_DIR: str = "input"
    APP_OUTPUT_DIR: str = "output"
    
    # Debug mode
    APP_DEBUG: bool = False
    
    # Model mappings
    _model_mapping: Dict[str, Optional[str]] = {}
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize configuration from environment."""
        load_environment()
        
        # Provider selection: antigravity (default) or openrouter
        cls.SCENOGRAFIA_PROVIDER = os.getenv("SCENOGRAFIA_PROVIDER", "antigravity").lower()

        # OpenRouter API key (only required when explicitly configured for openrouter)
        api_key = os.getenv("OPENROUTER_API_KEY")
        if cls.SCENOGRAFIA_PROVIDER == "openrouter" and not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required when SCENOGRAFIA_PROVIDER='openrouter'. Please set it in .env or environment."
            )
        cls.OPENROUTER_API_KEY = api_key
        
        # Optional: Base URL
        cls.OPENROUTER_BASE_URL = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1"
        )
        
        # Optional: Timeout
        timeout_env = os.getenv("OPENROUTER_TIMEOUT")
        if timeout_env:
            try:
                cls.OPENROUTER_TIMEOUT = float(timeout_env)
            except ValueError:
                cls.OPENROUTER_TIMEOUT = 60.0
        else:
            cls.OPENROUTER_TIMEOUT = 60.0
        
        # Optional: Enhancer Model
        cls.OPENROUTER_ENHANCER_MODEL = os.getenv(
            "OPENROUTER_ENHANCER_MODEL",
            "google/gemini-2.5-flash"
        )
        
        # Optional: Directories
        cls.APP_INPUT_DIR = os.getenv("APP_INPUT_DIR", "input")
        cls.APP_OUTPUT_DIR = os.getenv("APP_OUTPUT_DIR", "output")
        
        # Optional: Debug
        cls.APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
        
        # Initialize model mappings
        cls._initialize_model_mapping()
    
    @classmethod
    def _initialize_model_mapping(cls) -> None:
        """Initialize model ID mappings from environment."""
        cls._model_mapping = {
            GenerationMode.DRAFT.value: os.getenv("OPENROUTER_DRAFT_MODEL"),
            GenerationMode.STANDARD.value: os.getenv("OPENROUTER_STANDARD_MODEL"),
            GenerationMode.PRODUCTION.value: os.getenv("OPENROUTER_PRODUCTION_MODEL"),
            GenerationMode.VECTOR_READY.value: os.getenv("OPENROUTER_VECTOR_READY_MODEL"),
        }
    
    @classmethod
    def get_model_for_mode(cls, mode: GenerationMode) -> Optional[str]:
        """
        Get the model ID configured for a specific generation mode.
        
        Args:
            mode: GenerationMode value
            
        Returns:
            Model ID string or None if not configured
        """
        # Ensure mapping is initialized
        if not cls._model_mapping:
            cls._initialize_model_mapping()
        
        mode_str = mode.value if isinstance(mode, GenerationMode) else str(mode)
        return cls._model_mapping.get(mode_str)
    
    @classmethod
    def get_model_id(cls, mode: GenerationMode, override: Optional[str] = None) -> str:
        """
        Get the model ID to use for generation.
        
        Priority:
        1. Override from CLI/request
        2. Configuration for mode
        3. Fallback default
        
        Args:
            mode: GenerationMode
            override: Optional CLI override
            
        Returns:
            Model ID to use
        """
        if override:
            return override
        
        configured = cls.get_model_for_mode(mode)
        if configured:
            return configured
        
        # Fallback defaults based on active provider
        provider = getattr(cls, "SCENOGRAFIA_PROVIDER", "antigravity").lower()
        if provider in ("antigravity", "bridge", "local"):
            fallbacks = {
                GenerationMode.DRAFT: "antigravity/gemini-2.5-flash-image",
                GenerationMode.STANDARD: "antigravity/gemini-2.5-flash-image",
                GenerationMode.PRODUCTION: "antigravity/gemini-2.5-pro-image",
                GenerationMode.VECTOR_READY: "antigravity/gemini-2.5-pro-image",
            }
        else:
            fallbacks = {
                GenerationMode.DRAFT: "google/gemini-2.5-flash-image",
                GenerationMode.STANDARD: "google/gemini-2.5-flash-image",
                GenerationMode.PRODUCTION: "google/gemini-2.5-flash-image",
                GenerationMode.VECTOR_READY: "google/gemini-2.5-flash-image",
            }
        return fallbacks.get(mode, fallbacks[GenerationMode.STANDARD])

    @classmethod
    def get_timeout(cls) -> float:
        """Get the timeout in seconds for OpenRouter API requests."""
        return getattr(cls, "OPENROUTER_TIMEOUT", 60.0)
    
    @classmethod
    def get_all_mappings(cls) -> Dict[str, Optional[str]]:
        """
        Get all mode-to-model mappings.
        
        Returns:
            Dictionary mapping mode names to model IDs
        """
        if not cls._model_mapping:
            cls._initialize_model_mapping()
        return cls._model_mapping.copy()
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration.
        
        Returns:
            True if valid, raises exception otherwise
        """
        provider = getattr(cls, "SCENOGRAFIA_PROVIDER", "antigravity").lower()
        if provider == "openrouter":
            if not getattr(cls, "OPENROUTER_API_KEY", None):
                raise ValueError("OPENROUTER_API_KEY not set")
        
        # Ensure output directory exists
        Path(cls.APP_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        
        return True


# Initialize configuration when module is imported
try:
    Config.initialize()
except ValueError as e:
    # Allow module import even if config isn't ready
    # (useful for tests and dynamic initialization)
    pass
