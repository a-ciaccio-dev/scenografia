"""Tests for retry with backoff and configurable timeout in OpenRouterClient."""

from unittest.mock import MagicMock, Mock, patch
import httpx
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.config import Config
from scenografia.schemas.generation_schema import Orientation

# 1x1 transparent PNG in base64
TINY_PNG_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@patch('scenografia.tools.openrouter_client.httpx.Client')
def test_openrouter_retries_on_rate_limit(mock_client_class):
    """Verify that 429 status triggers retry and succeeds on subsequent 200 response."""
    # First call returns 429, second returns 200 with valid image
    mock_resp_429 = Mock(spec=httpx.Response)
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Rate limited"

    mock_resp_200 = Mock(spec=httpx.Response)
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "id": "gen-retry-123",
        "choices": [{"message": {"images": [{"image_url": {"url": TINY_PNG_B64}}]}}]
    }

    mock_client = MagicMock()
    mock_client.post.side_effect = [mock_resp_429, mock_resp_200]
    mock_client_class.return_value = mock_client

    client = OpenRouterClient(api_key="test-key")
    client.client = mock_client

    response = client.generate_image(
        prompt="Test scene with retry",
        model_id="test-model",
        orientation=Orientation.LANDSCAPE
    )

    assert response.error is None
    assert mock_client.post.call_count == 2
    assert response.image_data is not None


@patch('scenografia.tools.openrouter_client.httpx.Client')
def test_openrouter_uses_configured_timeout(mock_client_class):
    """Verify that Config.OPENROUTER_TIMEOUT is passed to post call."""
    mock_resp_200 = Mock(spec=httpx.Response)
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "id": "gen-timeout-123",
        "choices": [{"message": {"images": [{"image_url": {"url": TINY_PNG_B64}}]}}]
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp_200
    mock_client_class.return_value = mock_client

    # Temporarily set timeout in Config
    original_timeout = Config.OPENROUTER_TIMEOUT
    try:
        Config.OPENROUTER_TIMEOUT = 120.0
        client = OpenRouterClient(api_key="test-key")
        client.client = mock_client

        client.generate_image(
            prompt="Test scene with custom timeout",
            model_id="test-model",
            orientation=Orientation.LANDSCAPE
        )

        _, kwargs = mock_client.post.call_args
        assert kwargs.get("timeout") == 120.0
    finally:
        Config.OPENROUTER_TIMEOUT = original_timeout
