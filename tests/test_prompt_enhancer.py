"""Tests for PromptEnhancerAgent."""

import pytest
from unittest.mock import Mock, patch
from scenografia.agents.prompt_enhancer_agent import PromptEnhancerAgent
from scenografia.config import Config


class TestPromptEnhancerAgent:
    """Unit tests for PromptEnhancerAgent."""

    def test_enhance_empty_prompt_returns_empty_string(self):
        """Enhancing an empty prompt should return an empty string without calling the API."""
        mock_client = Mock()
        agent = PromptEnhancerAgent(client=mock_client)
        
        assert agent.enhance_prompt("") == ""
        assert agent.enhance_prompt("   ") == ""
        mock_client.generate_text.assert_not_called()

    def test_enhance_prompt_success(self):
        """Enhancing a valid prompt should call generate_text and return the result."""
        mock_client = Mock()
        mock_client.generate_text.return_value = "  An enhanced theatrical scenic description.  "
        agent = PromptEnhancerAgent(client=mock_client)

        result = agent.enhance_prompt("simple idea", model_id="override-model")
        
        assert result == "An enhanced theatrical scenic description."
        mock_client.generate_text.assert_called_once()
        _, kwargs = mock_client.generate_text.call_args
        assert kwargs["prompt"] == "simple idea"
        assert kwargs["model_id"] == "override-model"
        assert "theatrical" in kwargs["system_instruction"].lower()

    def test_enhance_prompt_uses_config_model_by_default(self):
        """Enhancing a prompt should default to Config.OPENROUTER_ENHANCER_MODEL or fallback."""
        mock_client = Mock()
        mock_client.generate_text.return_value = "Enhanced"
        agent = PromptEnhancerAgent(client=mock_client)

        with patch.object(Config, "OPENROUTER_ENHANCER_MODEL", "configured-model"):
            agent.enhance_prompt("concept")
            mock_client.generate_text.assert_called_once()
            _, kwargs = mock_client.generate_text.call_args
            assert kwargs["model_id"] == "configured-model"

    def test_enhance_prompt_fallback_on_error(self):
        """If client.generate_text raises an exception, the agent should return the raw prompt."""
        mock_client = Mock()
        mock_client.generate_text.side_effect = RuntimeError("API down")
        agent = PromptEnhancerAgent(client=mock_client)

        result = agent.enhance_prompt("original prompt")
        assert result == "original prompt"
