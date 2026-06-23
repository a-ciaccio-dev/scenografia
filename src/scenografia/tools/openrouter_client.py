"""
OpenRouter HTTP client for image generation via chat/completions.

Handles communication with OpenRouter API for image generation,
request/response mapping, and orientation-aware image configuration.
"""

import httpx
import base64
from typing import Optional, Dict, Any
from ..schemas.generation_schema import (
    ImageGenerationResponse,
    Orientation,
    GenerationMode
)
from ..config import Config


class OpenRouterClient:
    """HTTP client for OpenRouter image generation via chat/completions."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize image generation client.
        
        Args:
            api_key: API key (uses Config if not provided)
            base_url: API base URL (uses Config if not provided)
        """
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.base_url = (base_url or Config.OPENROUTER_BASE_URL).rstrip("/")
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0
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
        model_id: str = "google/gemini-2.5-flash-image",
        orientation: Orientation = Orientation.LANDSCAPE,
        input_image_bytes: Optional[bytes] = None
    ) -> ImageGenerationResponse:
        """
        Generate an image using OpenRouter chat/completions with modalities.
        
        Args:
            prompt: Main generation prompt
            negative_prompt: Negative constraints
            model_id: OpenRouter model ID (must support image output modality)
            orientation: Output orientation
            input_image_bytes: Optional bytes of a previous image to base generation on (img2img)
            
        Returns:
            ImageGenerationResponse with result
        """
        try:
            # Map orientation to aspect ratio
            aspect_ratio = self._map_orientation_to_aspect_ratio(orientation)
            
            if input_image_bytes:
                # Convert bytes to base64 data URL
                base64_str = base64.b64encode(input_image_bytes).decode("utf-8")
                refined_prompt = (
                    f"Use the attached reference image showing the current scenic layout and color palette. "
                    f"Generate a new theatrical scenic design that copies the composition, arrangement, and color choices "
                    f"of this reference image, but updates, enhances, or adds details according to this description: {prompt}"
                )
                content = [
                    {
                        "type": "text",
                        "text": refined_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_str}"
                        }
                    }
                ]
            else:
                content = prompt
            
            # Build request payload for OpenRouter chat/completions
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {
                    "aspect_ratio": aspect_ratio
                },
                "stream": False
            }
            
            # Make request to chat/completions endpoint
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60.0
            )
            
            # Handle HTTP errors
            if response.status_code != 200:
                # Sanitize error message (remove API key)
                error_text = response.text[:500]  # Limit error text length
                return ImageGenerationResponse(
                    error=f"API error: {response.status_code}",
                    model_used=model_id,
                    request_id="unknown"
                )
            
            data = response.json()
            
            # Parse response: choices[0].message.images[0].image_url.url
            try:
                message = data["choices"][0]["message"]
                images = message.get("images", [])
                
                if not images:
                    return ImageGenerationResponse(
                        error="No images in response",
                        model_used=model_id,
                        request_id="unknown"
                    )
                
                image_url_data = images[0].get("image_url", {})
                image_url = image_url_data.get("url", "")
                
                if not image_url:
                    return ImageGenerationResponse(
                        error="Empty image URL in response",
                        model_used=model_id,
                        request_id="unknown"
                    )
                
                # Handle base64 data URL or remote URL
                image_data = None
                if image_url.startswith("data:image/"):
                    # Decode base64 data URL
                    image_data = self._decode_base64_data_url(image_url)
                    if not image_data:
                        return ImageGenerationResponse(
                            error="Failed to decode base64 image data",
                            model_used=model_id,
                            request_id="unknown"
                        )
                elif image_url.startswith("http"):
                    # Download remote image
                    image_data = self._download_image_from_url(image_url)
                    if not image_data:
                        return ImageGenerationResponse(
                            error="Remote image URL download failed",
                            model_used=model_id,
                            request_id="unknown"
                        )
                else:
                    return ImageGenerationResponse(
                        error=f"Unsupported image URL format",
                        model_used=model_id,
                        request_id="unknown"
                    )
                
                # Get request ID from response if available
                request_id = data.get("id", "unknown")
                
                return ImageGenerationResponse(
                    image_url=image_url,
                    image_data=image_data,
                    model_used=model_id,
                    request_id=request_id
                )
                
            except (KeyError, IndexError, TypeError) as e:
                return ImageGenerationResponse(
                    error=f"Failed to parse response structure",
                    model_used=model_id,
                    request_id="unknown"
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
    def _map_orientation_to_aspect_ratio(orientation: Orientation) -> str:
        """
        Map orientation to aspect ratio string for OpenRouter image_config.
        
        Args:
            orientation: Target orientation
            
        Returns:
            Aspect ratio string (e.g., "16:9")
        """
        mapping = {
            Orientation.PORTRAIT: "9:16",
            Orientation.LANDSCAPE: "16:9",
            Orientation.SQUARE: "1:1",
        }
        return mapping.get(orientation, "16:9")
    
    @staticmethod
    def _map_orientation_to_config(orientation: Orientation) -> Dict[str, str]:
        """
        Map orientation to image_config dict format.
        Used for compatibility with tests and ProviderAdapter.
        
        Args:
            orientation: Target orientation
            
        Returns:
            Config dict with aspect_ratio
        """
        aspect_ratio = OpenRouterClient._map_orientation_to_aspect_ratio(orientation)
        return {"aspect_ratio": aspect_ratio}
    
    @staticmethod
    def _decode_base64_data_url(data_url: str) -> Optional[bytes]:
        """
        Decode a base64 data URL to image bytes.
        
        Args:
            data_url: Data URL string (e.g., "data:image/png;base64,ABC...")
            
        Returns:
            Image bytes or None if decode fails
        """
        try:
            # Extract base64 part after the comma
            if "," not in data_url:
                return None
            
            base64_part = data_url.split(",", 1)[1]
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_part)
            return image_bytes
        except Exception as e:
            return None
    
    def _download_image_from_url(self, url: str) -> Optional[bytes]:
        """
        Download image from remote URL.
        
        Args:
            url: Remote image URL
            
        Returns:
            Image bytes or None if download fails
        """
        try:
            response = self.client.get(url, timeout=30.0)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            return None
    
    def fetch_image_from_url(self, url: str) -> Optional[bytes]:
        """
        Fetch image data from URL (legacy method name for compatibility).
        Delegates to _download_image_from_url.
        
        Args:
            url: Image URL
            
        Returns:
            Image bytes or None if fetch fails
        """
        return self._download_image_from_url(url)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_id: str = "google/gemini-2.5-flash",
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """
        Generate a text response using OpenRouter chat/completions.
        
        Args:
            prompt: User message content
            system_instruction: Optional system instruction
            model_id: Model identifier
            image_bytes: Optional bytes of an image to analyze
            
        Returns:
            Generated text content
        """
        try:
            messages = []
            if system_instruction:
                messages.append({
                    "role": "system",
                    "content": system_instruction
                })
            
            if image_bytes:
                base64_str = base64.b64encode(image_bytes).decode("utf-8")
                content = [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_str}"
                        }
                    }
                ]
            else:
                content = prompt

            messages.append({
                "role": "user",
                "content": content
            })
            
            payload = {
                "model": model_id,
                "messages": messages,
                "stream": False
            }
            
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=45.0
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"OpenRouter API error {response.status_code}: {response.text[:200]}")
                
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Text generation failed: {str(e)}")


class ProviderAdapter:
    """
    Adapter for provider-specific image generation configuration.
    
    Translates generation parameters to OpenRouter chat/completions format.
    Note: Only used by tests, not in the main generation path.
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
        Build a complete image generation request for OpenRouter chat/completions.
        
        Args:
            prompt: Main prompt
            negative_prompt: Negative constraints
            model_id: OpenRouter model ID
            orientation: Output orientation
            generation_mode: Generation mode (for future use)
            
        Returns:
            Complete request dictionary in chat/completions format
        """
        # Map orientation to aspect ratio
        aspect_ratio = OpenRouterClient._map_orientation_to_aspect_ratio(orientation)
        
        # Build OpenRouter chat/completions format request
        request = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": aspect_ratio
            },
            "stream": False
        }
        
        return request
