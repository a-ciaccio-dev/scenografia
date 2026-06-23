"""Tests for the text generation pipeline orchestration."""

from scenografia.schemas.generation_schema import (
    GenerationMode,
    GenerationRequest,
    ImageGenerationResponse,
    Orientation,
)
from scenografia.schemas.validation_schema import ValidationReport


class StubBriefAgent:
    def create_from_text(self, request: GenerationRequest):
        return {
            "scene_description": request.text_prompt,
            "orientation": request.orientation,
            "generation_mode": request.mode,
            "style_constraints": ["full color"],
            "negative_constraints": ["no gradients"],
            "composition_guidance": ["use landscape staging"],
            "input_source": "text",
        }


class StubPromptEngineerAgent:
    def build_prompt_package(self, brief):
        return {
            "final_prompt": f"Prompt: {brief['scene_description']} ({brief['orientation'].value})",
            "negative_prompt": "no gradients",
            "orientation_applied": True,
        }

    def refine_prompt_package(self, prompt_package, issues):
        return prompt_package


class StubImageGenerationAgent:
    def generate(self, request: GenerationRequest, prompt_package, brief, input_image_bytes=None):
        return ImageGenerationResponse(
            image_url="https://example.com/final.png",
            image_data=b"fake-image",
            model_used="demo-model",
            request_id="req-123",
        )


class StubStyleComplianceAgent:
    def validate_text_run(self, brief, prompt_package, response):
        return ValidationReport(
            report_id="val-001",
            run_id=response.request_id,
            orientation=brief["orientation"],
            style_compliant=True,
            artifacts_complete=True,
            issues=[],
        )


class StubOutputManager:
    def __init__(self):
        self.saved_payload = None

    def persist_text_run(self, brief, prompt_package, response, validation_report, metadata=None, output_dir=None, processed_sketch_path=None):
        self.saved_payload = {
            "brief": brief,
            "prompt_package": prompt_package,
            "response": response,
            "validation_report": validation_report,
        }
        return {
            "output_dir": "output/run-003",
            "image_path": "output/run-003/final.png",
            "prompt_path": "output/run-003/prompt.txt",
            "negative_prompt_path": "output/run-003/negative_prompt.txt",
            "brief_path": "output/run-003/brief.json",
            "metadata_path": "output/run-003/generation_response.json",
            "validation_path": "output/run-003/validation_report.json",
        }


def test_text_generation_pipeline_persists_prompt_metadata_and_validation_artifacts():
    """Pipeline should orchestrate prompt creation, generation, validation, and persistence."""
    from scenografia.agents.image_generation_agent import TextGenerationService

    output_manager = StubOutputManager()
    service = TextGenerationService(
        brief_agent=StubBriefAgent(),
        prompt_engineer=StubPromptEngineerAgent(),
        image_generator=StubImageGenerationAgent(),
        style_validator=StubStyleComplianceAgent(),
        output_manager=output_manager,
    )

    result = service.run_text_generation(
        prompt="Crimson velvet stage curtains framing a town square",
        mode=GenerationMode.STANDARD,
        orientation=Orientation.LANDSCAPE,
        model=None,
    )

    assert result["output_dir"] == "output/run-003"
    assert output_manager.saved_payload is not None
    assert output_manager.saved_payload["brief"]["orientation"] == Orientation.LANDSCAPE
    assert output_manager.saved_payload["prompt_package"]["orientation_applied"] is True
    assert output_manager.saved_payload["response"].request_id == "req-123"
    assert output_manager.saved_payload["validation_report"].orientation == Orientation.LANDSCAPE


def test_text_generation_pipeline_builds_request_with_selected_mode_and_orientation():
    """Pipeline should construct a GenerationRequest that preserves mode and orientation."""
    from scenografia.agents.image_generation_agent import TextGenerationService

    class CapturingBriefAgent(StubBriefAgent):
        def __init__(self):
            self.seen_request = None

        def create_from_text(self, request: GenerationRequest):
            self.seen_request = request
            return super().create_from_text(request)

    brief_agent = CapturingBriefAgent()
    service = TextGenerationService(
        brief_agent=brief_agent,
        prompt_engineer=StubPromptEngineerAgent(),
        image_generator=StubImageGenerationAgent(),
        style_validator=StubStyleComplianceAgent(),
        output_manager=StubOutputManager(),
    )

    service.run_text_generation(
        prompt="Painted castle battlements",
        mode=GenerationMode.PRODUCTION,
        orientation=Orientation.PORTRAIT,
        model="custom/model",
    )

    assert brief_agent.seen_request is not None
    assert brief_agent.seen_request.mode == GenerationMode.PRODUCTION
    assert brief_agent.seen_request.orientation == Orientation.PORTRAIT
    assert brief_agent.seen_request.model_id == "custom/model"