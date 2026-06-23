"""Tests for OpenRouter client and provider adapter."""

import pytest
import base64
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
    """Test orientation to aspect ratio mapping."""
    
    def test_portrait_maps_to_aspect_ratio(self):
        """Portrait orientation should map to 9:16 aspect ratio."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.PORTRAIT)
        assert config["aspect_ratio"] == "9:16"
    
    def test_landscape_maps_to_aspect_ratio(self):
        """Landscape orientation should map to 16:9 aspect ratio."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.LANDSCAPE)
        assert config["aspect_ratio"] == "16:9"
    
    def test_square_maps_to_aspect_ratio(self):
        """Square orientation should map to 1:1 aspect ratio."""
        config = OpenRouterClient._map_orientation_to_config(Orientation.SQUARE)
        assert config["aspect_ratio"] == "1:1"


class TestImageGeneration:
    """Test image generation with mocked HTTP (OpenRouter chat/completions)."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_success_with_base64_data_url(self, mock_client_class):
        """Should handle successful generation with base64 data URL."""
        # Mock base64-encoded image
        fake_image_bytes = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"
        base64_encoded = base64.b64encode(fake_image_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_encoded}"
        
        # Mock the HTTP response for OpenRouter chat/completions
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        response = client.generate_image(
            prompt="Test prompt",
            model_id="google/gemini-2.5-flash-image",
            orientation=Orientation.LANDSCAPE
        )
        
        assert response.image_url == data_url
        assert response.image_data == fake_image_bytes
        assert response.model_used == "google/gemini-2.5-flash-image"
        assert response.request_id == "gen-123"
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_api_error(self, mock_client_class):
        """Should handle API errors without exposing API key."""
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
        assert "test-key" not in response.error  # API key must not be exposed
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_includes_modalities_in_request(self, mock_client_class):
        """Should include modalities and image_config in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "choices": [{"message": {"images": [{"image_url": {"url": "data:image/png;base64,ABC"}}]}}]
        }
        
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
        
        # Verify the request structure
        call_args = mock_client.post.call_args
        assert call_args[0][0].endswith("/chat/completions")  # Check endpoint
        
        payload = call_args[1]["json"]
        assert payload["model"] == "test-model"
        assert "messages" in payload
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "Test"
        assert payload["modalities"] == ["image", "text"]
        assert "image_config" in payload
        assert payload["image_config"]["aspect_ratio"] == "9:16"  # Portrait
        assert payload["stream"] is False
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_landscape_aspect_ratio(self, mock_client_class):
        """Should send landscape 16:9 aspect ratio."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "choices": [{"message": {"images": [{"image_url": {"url": "data:image/png;base64,ABC"}}]}}]
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        client.generate_image(
            prompt="Test",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )
        
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["image_config"]["aspect_ratio"] == "16:9"
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_square_aspect_ratio(self, mock_client_class):
        """Should send square 1:1 aspect ratio."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "choices": [{"message": {"images": [{"image_url": {"url": "data:image/png;base64,ABC"}}]}}]
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        client.generate_image(
            prompt="Test",
            model_id="test-model",
            orientation=Orientation.SQUARE
        )
        
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["image_config"]["aspect_ratio"] == "1:1"
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_no_images_in_response(self, mock_client_class):
        """Should handle response with no images."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-123",
            "choices": [{"message": {"images": []}}]
        }
        
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
        assert "No images" in response.error


class TestProviderAdapter:
    """Test provider adapter for request building (OpenRouter chat/completions format)."""
    
    def test_build_image_request_complete(self):
        """Should build complete image request in chat/completions format."""
        request = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="Avoid",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE,
            generation_mode=GenerationMode.STANDARD
        )
        
        assert request["model"] == "test-model"
        assert request["messages"][0]["role"] == "user"
        assert request["messages"][0]["content"] == "Test"
        assert request["modalities"] == ["image", "text"]
        assert request["image_config"]["aspect_ratio"] == "16:9"
        assert request["stream"] is False
    
    def test_build_image_request_orientation_mapping(self):
        """Should correctly map orientation to aspect ratio."""
        # Portrait
        request_portrait = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="",
            model_id="test-model",
            orientation=Orientation.PORTRAIT,
            generation_mode=GenerationMode.STANDARD
        )
        assert request_portrait["image_config"]["aspect_ratio"] == "9:16"
        
        # Square
        request_square = ProviderAdapter.build_image_request(
            prompt="Test",
            negative_prompt="",
            model_id="test-model",
            orientation=Orientation.SQUARE,
            generation_mode=GenerationMode.STANDARD
        )
        assert request_square["image_config"]["aspect_ratio"] == "1:1"


class TestBase64DataURLDecoding:
    """Test base64 data URL decoding."""
    
    def test_decode_base64_data_url(self):
        """Should correctly decode base64 data URL."""
        fake_image = b"fake-image-bytes"
        base64_encoded = base64.b64encode(fake_image).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_encoded}"
        
        decoded = OpenRouterClient._decode_base64_data_url(data_url)
        assert decoded == fake_image
    
    def test_decode_invalid_data_url(self):
        """Should return None for invalid data URL."""
        result = OpenRouterClient._decode_base64_data_url("invalid-url")
        assert result is None


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
        assert "test-key" not in response.error  # API key must not be exposed


class TestImageToImageGeneration:
    """Test image-to-image multimodal generation requests."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_image_with_input_image_bytes(self, mock_client_class):
        """Should format request with multimodal message contents when input_image_bytes are provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "gen-img2img",
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "image_url": {
                                    "url": "data:image/png;base64,ZmFrZS1pbWFnZQ=="
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        fake_input_image = b"previous-image-data"
        
        response = client.generate_image(
            prompt="Add a steampunk window",
            model_id="google/gemini-2.5-flash-image",
            orientation=Orientation.LANDSCAPE,
            input_image_bytes=fake_input_image
        )
        
        assert response.error is None
        assert response.request_id == "gen-img2img"
        
        # Verify the payload structure
        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        json_payload = kwargs["json"]
        
        # Messages content should be a list
        messages = json_payload["messages"]
        assert len(messages) == 1
        content = messages[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        
        # One text block and one image_url block
        assert content[0]["type"] == "text"
        assert "steampunk" in content[0]["text"]
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


class TestGenerateText:
    """Test text generation (OpenRouter chat/completions)."""
    
    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_text_simple(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Enhanced Prompt"
                    }
                }
            ]
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        res = client.generate_text("Concept prompt")
        assert res == "Enhanced Prompt"
        
        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        json_payload = kwargs["json"]
        assert json_payload["model"] == "google/gemini-2.5-flash"
        assert json_payload["messages"][0]["role"] == "user"
        assert json_payload["messages"][0]["content"] == "Concept prompt"

    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_text_with_system_instruction_and_image(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Enhanced with image analysis"
                    }
                }
            ]
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        res = client.generate_text(
            prompt="Concept prompt",
            system_instruction="System rule",
            model_id="custom-enhancer",
            image_bytes=b"fake-image"
        )
        assert res == "Enhanced with image analysis"
        
        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        json_payload = kwargs["json"]
        assert json_payload["model"] == "custom-enhancer"
        
        messages = json_payload["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System rule"
        
        assert messages[1]["role"] == "user"
        content = messages[1]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Concept prompt"
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")

    @patch('scenografia.tools.openrouter_client.httpx.Client')
    def test_generate_text_error_handling(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client
        
        with pytest.raises(RuntimeError) as exc_info:
            client.generate_text("Concept prompt")
        assert "OpenRouter API error 500" in str(exc_info.value)

