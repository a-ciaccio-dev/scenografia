"""
OpenRouter HTTP client and provider adapter for image generation.

Handles communication with OpenRouter API, request/response mapping,
and orientation-aware image configuration.
"""

import httpx
from typing import Optional, Dict, Any
import asyncio
from ..schemas.generation_schema import (
    ImageGenerationResponse,
    Orientation,
    GenerationMode
)
from ..config import Config


class OpenRouterClient:
    """HTTP client for OpenRouter image generation API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (uses Config if not provided)
            base_url: OpenRouter base URL (uses Config if not provided)
        """
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.base_url = (base_url or Config.OPENROUTER_BASE_URL).rstrip("/")
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: str = "meta-llama/llama-2-70b",
        orientation: Orientation = Orientation.LANDSCAPE
    ) -> ImageGenerationResponse:
        """
        Generate an image using OpenRouter.
        
        Args:
            prompt: Main generation prompt
            negative_prompt: Negative constraints
            model_id: Model to use
            orientation: Output orientation
            
        Returns:
            ImageGenerationResponse with result
        """
        try:
            # Build request payload
            payload = {
                "model": model_id,
                "prompt": prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Add negative prompt if provided
            if negative_prompt:
                # Many models don't support negative_prompt, but include it if possible
                payload["negative_prompt"] = negative_prompt
            
            # Map orientation to provider-specific configuration
            image_config = self._map_orientation_to_config(orientation)
            payload.update(image_config)
            
            # Make request
            response = self.client.post(
                f"{self.base_url}/images/generations",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                return ImageGenerationResponse(
                    error=f"API error: {response.status_code} - {response.text}",
                    model_used=model_id,
                    request_id="unknown"
                )
            
            data = response.json()
            
            # Extract image from response
            image_url = None
            image_data = None
            
            if "data" in data and len(data["data"]) > 0:
                image_url = data["data"][0].get("url")
            
            return ImageGenerationResponse(
                image_url=image_url,
                image_data=image_data,
                model_used=model_id,
                request_id=data.get("id", "unknown")
            )
            
        except httpx.RequestError as e:
            return ImageGenerationResponse(
                error=f"Request failed: {str(e)}",
                model_used=model_id,
                request_id="unknown"
            )
        except Exception as e:
            return ImageGenerationResponse(
                error=f"Unexpected error: {str(e)}",
                model_used=model_id,
                request_id="unknown"
            )
    
    @staticmethod
    def _map_orientation_to_config(orientation: Orientation) -> Dict[str, Any]:
        """
        Map orientation to provider-specific image configuration.
        
        Args:
            orientation: Target orientation
            
        Returns:
            Configuration dict for the API request
        """
        # OpenRouter uses width x height for aspect ratio
        # Common sizes:
        aspect_ratios = {
            Orientation.PORTRAIT: {"width": 768, "height": 1024},
            Orientation.LANDSCAPE: {"width": 1024, "height": 768},
            Orientation.SQUARE: {"width": 1024, "height": 1024},
        }
        
        config = aspect_ratios.get(orientation, {"width": 1024, "height": 768})
        return config
    
    def fetch_image_from_url(self, url: str) -> Optional[bytes]:
        """
        Fetch image data from URL.
        
        Args:
            url: Image URL
            
        Returns:
            Image bytes or None if fetch fails
        """
        try:
            response = self.client.get(url, timeout=30.0)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Error fetching image: {e}")
        
        return None


class ProviderAdapter:
    """
    Adapter for provider-specific image generation configuration.
    
    Translates generation parameters to provider-specific formats.
    """
    
    @staticmethod
    def build_image_request(
        prompt: str,
        negative_prompt: str,
        model_id: str,
        orientation: Orientation,
        generation_mode: GenerationMode = GenerationMode.STANDARD
    ) -> Dict[str, Any]:
        """
        Build a complete image generation request for the provider.
        
        Args:
            prompt: Main prompt
            negative_prompt: Negative constraints
            model_id: Model ID
            orientation: Output orientation
            generation_mode: Generation mode
            
        Returns:
            Complete request dictionary
        """
        # Base request
        request = {
            "model": model_id,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
        }
        
        # Add orientation-specific configuration
        aspect_config = OpenRouterClient._map_orientation_to_config(orientation)
        request.update(aspect_config)
        
        # Add mode-specific quality settings
        quality_settings = ProviderAdapter._get_quality_settings(generation_mode)
        request.update(quality_settings)
        
        return request
    
    @staticmethod
    def _get_quality_settings(mode: GenerationMode) -> Dict[str, Any]:
        """
        Get quality/speed settings based on generation mode.
        
        Args:
            mode: Generation mode
            
        Returns:
            Quality settings dict
        """
        settings = {
            GenerationMode.DRAFT: {
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
            },
            GenerationMode.STANDARD: {
                "num_inference_steps": 30,
                "guidance_scale": 8.0,
            },
            GenerationMode.PRODUCTION: {
                "num_inference_steps": 50,
                "guidance_scale": 8.5,
            },
            GenerationMode.VECTOR_READY: {
                "num_inference_steps": 40,
                "guidance_scale": 9.0,
            },
        }
        return settings.get(mode, settings[GenerationMode.STANDARD])
