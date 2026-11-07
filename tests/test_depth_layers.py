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


def test_text_generation_service_injects_layer_into_prompt(tmp_path):
    """Test TextGenerationService injects depth layer instruction into prompt."""
    from unittest.mock import MagicMock
    from scenografia.services.text_generation_service import TextGenerationService
    from scenografia.schemas.generation_schema import GenerationMode, Orientation

    mock_brief_agent = MagicMock()
    mock_brief_agent.create_from_text.return_value = {
        "scene_description": "Palace",
        "style_requirements": "Theatrical",
        "orientation": "landscape",
    }

    pkg = {
        "final_prompt": "Palace prompt",
        "negative_prompt": "Negative",
        "brief": {},
    }
    mock_prompt_eng = MagicMock()
    mock_prompt_eng.generate_prompt_package.return_value = pkg
    mock_prompt_eng.refine_prompt_package.return_value = pkg

    mock_generator = MagicMock()
    mock_response = MagicMock()
    mock_response.image_data = b"fake"
    mock_response.request_id = "req_1"
    mock_response.model_used = "m"
    mock_response.image_url = None
    mock_generator.generate.return_value = mock_response

    mock_validator = MagicMock()
    mock_output_manager = MagicMock()
    mock_output_manager.persist_text_run.return_value = {"output_dir": tmp_path}

    service = TextGenerationService(
        brief_agent=mock_brief_agent,
        prompt_engineer=mock_prompt_eng,
        image_generator=mock_generator,
        style_validator=mock_validator,
        output_manager=mock_output_manager,
    )

    service.run_text_generation(
        prompt="Palace",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        model=None,
        layer="background",
    )

    mock_brief_agent.create_from_text.assert_called_once()
    req = mock_brief_agent.create_from_text.call_args[0][0]
    assert "Fondale" in req.text_prompt


def test_cli_generate_accepts_layer_option(tmp_path):
    """Test CLI generate command accepts --layer option."""
    from unittest.mock import patch
    from typer.testing import CliRunner
    from scenografia.main import app

    runner = CliRunner()
    mock_result = {
        "output_dir": tmp_path,
        "image_path": tmp_path / "final.png",
        "prompt_path": tmp_path / "prompt.txt",
    }

    with patch("scenografia.services.text_generation_service.TextGenerationService.run_text_generation", return_value=mock_result) as mock_gen:
        result = runner.invoke(app, [
            "generate",
            "--prompt", "Enchanted garden",
            "--mode", "standard",
            "--orientation", "landscape",
            "--layer", "foreground",
        ])

        assert result.exit_code == 0
        assert mock_gen.call_args.kwargs.get("layer") == "foreground"
