"""Tests for OpenRouter client and provider adapter."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scenografia.tools.openrouter_client import (
    OpenRouterClient,
    ProviderAdapter
)
from scenografia.schemas.generation_schema import (
    Orientation,
    GenerationMode
)


class TestOpenRouterClientInitialization:
    """Test OpenRouter client initialization."""
    
    def test_client_initializes_with_api_key(self):
        """Client should initialize with API key."""
        client = OpenRouterClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
    
    def test_client_initializes_with_default_url(self):
        """Client should use default OpenRouter URL."""
        client = OpenRouterClient(api_key="test-key")
        assert "openrouter.ai" in client.base_url
    
    def test_client_initializes_with_custom_url(self):
        """Client should accept custom base URL."""
        client = OpenRouterClient(
            api_key="test-key",
            base_url="https://custom.api/v1"
        )
        assert "custom.api" in client.base_url
    
    def test_client_context_manager(self):
        """Client should work as context manager."""
        with OpenRouterClient(api_key="test-key") as client:
            assert client is not None


class TestOrientationMapping:
    """Test orientation to provider configuration mapping."""
    
    def test_portrait_maps_to_config(self):
        """Portrait orientation should map to config."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.PORTRAIT)
        assert "height" in config
        assert "width" in config
        assert config["height"] > config["width"]  # Taller than wide
    
    def test_landscape_maps_to_config(self):
        """Landscape orientation should map to config."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.LANDSCAPE)
        assert config["width"] > config["height"]  # Wider than tall
    
    def test_square_maps_to_config(self):
        """Square orientation should map to config."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.SQUARE)
        assert config["width"] == config["height"]


class TestImageGeneration:
    """Test image generation with mocked HTTP."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_success(self, mock_client_class):
        """Should handle successful generation."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "data": [{"url": "https://example.com/image.png"}]
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        response = client.generate_image(
            prompt="Test prompt",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )
        
        assert response.image_url == "https://example.com/image.png"
        assert response.model_used == "test-model"
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_api_error(self, mock_client_class):
        """Should handle API errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        response = client.generate_image(
            prompt="Test",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )
        
        assert response.error is not None
        assert "401" in response.error
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_includes_orientation_in_request(self, mock_client_class):
        """Should include orientation config in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "gen-123", "data": [{"url": "url"}]}
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        client.generate_image(
            prompt="Test",
            model_id="test-model",
            orientation=Orientation.PORTRAIT
        )
        
        # Verify the request included orientation config
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert "height" in payload
        assert "width" in payload
        assert payload["height"] > payload["width"]


class TestProviderAdapter:
    """Test provider adapter for request building."""
    
    def test_build_image_request_complete(self):
        """Should build complete image request."""
        request = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="Avoid",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE,
            generation_mode=GenerationMode.STANDARD
        )
        
        assert request["prompt"] == "Test"
        assert request["negative_prompt"] == "Avoid"
        assert request["model"] == "test-model"
        assert "width" in request
        assert "height" in request
    
    def test_quality_settings_for_draft_mode(self):
        """Should use draft settings for draft mode."""
        request = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="Avoid",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE,
            generation_mode=GenerationMode.DRAFT
        )
        
        assert request["num_inference_steps"] <= 30  # Draft is faster
    
    def test_quality_settings_for_production_mode(self):
        """Should use production settings for production mode."""
        request = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="Avoid",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE,
            generation_mode=GenerationMode.PRODUCTION
        )
        
        assert request["num_inference_steps"] >= 40  # Production is higher quality


class TestNegativePromptHandling:
    """Test negative prompt handling."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_with_negative_prompt(self, mock_client_class):
        """Should include negative prompt in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "data": [{"url": "url"}]}
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        client.generate_image(
            prompt="Test",
            negative_prompt="Avoid blur and gradients",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )
        
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert "negative_prompt" in payload
        assert "blur" in payload["negative_prompt"]


class TestClientErrorHandling:
    """Test error handling in client."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_handle_network_error(self, mock_client_class):
        """Should handle network errors."""
        import httpx
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Network error")
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        response = client.generate_image(
            prompt="Test",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )
        
        assert response.error is not None
        assert "Request failed" in response.error
