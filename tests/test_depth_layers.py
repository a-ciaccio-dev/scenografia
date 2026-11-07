"""
Unit tests for theatrical depth layering templates and PromptEnhancerAgent extensions.
"""

from unittest.mock import MagicMock
import pytest

from scenografia.agents.prompt_enhancer_agent import PromptEnhancerAgent
from scenografia.tools.prompt_templates import (
    DEPTH_LAYER_INSTRUCTIONS,
    DEPTH_LAYERS,
    get_depth_layer_instruction,
)


def test_depth_layers_definitions():
    """Verify definitions and instructions exist for all theatrical layers."""
    expected_layers = {"all", "foreground", "midground", "background"}
    assert set(DEPTH_LAYERS.keys()) == expected_layers
    assert set(DEPTH_LAYER_INSTRUCTIONS.keys()) == expected_layers

    # Check non-empty instructions for specific planes
    assert len(get_depth_layer_instruction("background")) > 10
    assert len(get_depth_layer_instruction("midground")) > 10
    assert len(get_depth_layer_instruction("foreground")) > 10
    assert get_depth_layer_instruction("all") == ""
    assert get_depth_layer_instruction("UNKNOWN") == ""


def test_prompt_enhancer_injects_layer_instruction():
    """Verify PromptEnhancerAgent injects depth layer constraint into system instruction."""
    mock_client = MagicMock()
    mock_client.generate_text.return_value = "Enhanced scenic description with quinte"

    enhancer = PromptEnhancerAgent(client=mock_client)
    res = enhancer.enhance_prompt(
        raw_prompt="Ancient greek palace",
        layer="foreground",
    )

    assert res == "Enhanced scenic description with quinte"
    mock_client.generate_text.assert_called_once()
    call_kwargs = mock_client.generate_text.call_args.kwargs
    system_inst = call_kwargs["system_instruction"]
    assert "THEATRICAL DEPTH LAYER CONSTRAINT" in system_inst
    assert "Quinte e Cieli" in system_inst


def test_prompt_enhancer_default_layer_does_not_inject_layer_constraint():
    """Verify PromptEnhancerAgent with layer='all' does not restrict layer."""
    mock_client = MagicMock()
    mock_client.generate_text.return_value = "Full scenic backdrop"

    enhancer = PromptEnhancerAgent(client=mock_client)
    res = enhancer.enhance_prompt(
        raw_prompt="Forest",
        layer="all",
    )

    assert res == "Full scenic backdrop"
    mock_client.generate_text.assert_called_once()
    system_inst = mock_client.generate_text.call_args.kwargs["system_instruction"]
    assert "THEATRICAL DEPTH LAYER CONSTRAINT" not in system_inst
