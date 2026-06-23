"""Generation orchestration for text and sketch workflows."""

from pathlib import Path

from scenografia.agents.brief_agent import BriefAgent
from scenografia.agents.prompt_engineer_agent import PromptEngineerAgent
from scenografia.agents.sketch_interpreter_agent import SketchInterpreterAgent
from scenografia.agents.style_compliance_agent import StyleComplianceAgent
from scenografia.config import Config
from scenografia.schemas.generation_schema import GenerationMode, GenerationRequest, Orientation
from scenografia.schemas.validation_schema import GenerationMetadata
from scenografia.tools.openrouter_client import OpenRouterClient
from scenografia.tools.output_manager import OutputManager


class ImageGenerationAgent:
    """Provider-facing image generation agent."""

    def __init__(self, client: OpenRouterClient | None = None):
        self.client = client or OpenRouterClient()

    def generate(self, request: GenerationRequest, prompt_package: dict, brief: dict, input_image_bytes: bytes | None = None):
        """Send the final prompt package to OpenRouter."""
        model_id = Config.get_model_id(request.mode, request.model_id)
        response = self.client.generate_image(
            prompt=prompt_package["final_prompt"],
            negative_prompt=prompt_package["negative_prompt"],
            model_id=model_id,
            orientation=request.orientation,
            input_image_bytes=input_image_bytes,
        )

        if response.error:
            raise RuntimeError(response.error)

        if response.image_data is None and response.image_url:
            response.image_data = self.client.fetch_image_from_url(response.image_url)

        if not response.image_data:
            raise RuntimeError("Image generation did not return image bytes")

        return response


class TextGenerationService:
    """Orchestrate the text-mode generation pipeline."""

    def __init__(
        self,
        brief_agent: BriefAgent | None = None,
        prompt_engineer: PromptEngineerAgent | None = None,
        image_generator: ImageGenerationAgent | None = None,
        style_validator: StyleComplianceAgent | None = None,
        output_manager: OutputManager | None = None,
    ):
        self.brief_agent = brief_agent or BriefAgent()
        self.prompt_engineer = prompt_engineer or PromptEngineerAgent()
        self.image_generator = image_generator
        self.style_validator = style_validator or StyleComplianceAgent()
        self.output_manager = output_manager or OutputManager()

    def _get_image_generator(self) -> ImageGenerationAgent:
        """Instantiate the provider agent lazily for testability."""
        if self.image_generator is None:
            self.image_generator = ImageGenerationAgent()
        return self.image_generator

    def run_text_generation(
        self,
        prompt: str,
        mode: GenerationMode | str,
        orientation: Orientation,
        model: str | None,
        style: str | None = "Default",
        progress_callback: callable = None,
        input_image_bytes: bytes | None = None,
    ) -> dict:
        """Execute the text-mode generation pipeline end to end."""
        if progress_callback:
            progress_callback("brief")
        normalized_mode = mode if isinstance(mode, GenerationMode) else GenerationMode(mode)
        request = GenerationRequest(
            input_type="text",
            text_prompt=prompt,
            mode=normalized_mode,
            orientation=orientation,
            model_id=model,
            selected_style=style or "Default",
        )
        brief = self.brief_agent.create_from_text(request)
        
        if progress_callback:
            progress_callback("prompt")
        prompt_package = self.prompt_engineer.build_prompt_package(brief)
        
        # generate -> validate -> refine -> regenerate loop
        from scenografia.tools.style_validator import StyleValidator
        max_attempts = 3
        response = None
        for attempt in range(max_attempts):
            style_valid, style_issues = StyleValidator.validate_style_contract(prompt_package["final_prompt"])
            neg_valid, neg_issues = StyleValidator.validate_negative_constraints(prompt_package["negative_prompt"])
            issues = [*style_issues, *neg_issues]
            
            if issues:
                if progress_callback:
                    progress_callback("refine")
                if hasattr(self.prompt_engineer, "refine_prompt_package"):
                    prompt_package = self.prompt_engineer.refine_prompt_package(prompt_package, issues)
            
            try:
                if progress_callback:
                    progress_callback("generate")
                generator = self._get_image_generator()
                import inspect
                sig = inspect.signature(generator.generate)
                if "input_image_bytes" in sig.parameters:
                    response = generator.generate(request, prompt_package, brief, input_image_bytes=input_image_bytes)
                else:
                    response = generator.generate(request, prompt_package, brief)
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                if hasattr(self.prompt_engineer, "refine_prompt_package"):
                    prompt_package = self.prompt_engineer.refine_prompt_package(prompt_package, [f"Error: {str(e)}"])

        if progress_callback:
            progress_callback("validate")
        validation_report = self.style_validator.validate_text_run(brief, prompt_package, response)
        metadata = GenerationMetadata(
            run_id=response.request_id,
            input_type="text",
            original_prompt=prompt,
            orientation=orientation,
            generation_mode=normalized_mode,
            model_id=response.model_used,
            brief=brief,
            final_prompt=prompt_package["final_prompt"],
            negative_prompt=prompt_package["negative_prompt"],
            image_url=response.image_url,
        )
        try:
            if progress_callback:
                progress_callback("persist")
            return self.output_manager.persist_text_run(
                brief=brief,
                prompt_package=prompt_package,
                response=response,
                validation_report=validation_report,
                metadata=metadata,
            )
        except TypeError:
            return self.output_manager.persist_text_run(
                brief,
                prompt_package,
                response,
                validation_report,
            )


class SketchGenerationService:
    """Orchestrate the sketch-mode generation pipeline."""

    def __init__(
        self,
        brief_agent: BriefAgent | None = None,
        prompt_engineer: PromptEngineerAgent | None = None,
        image_generator: ImageGenerationAgent | None = None,
        style_validator: StyleComplianceAgent | None = None,
        output_manager: OutputManager | None = None,
        sketch_interpreter: SketchInterpreterAgent | None = None,
    ):
        self.brief_agent = brief_agent or BriefAgent()
        self.prompt_engineer = prompt_engineer or PromptEngineerAgent()
        self.image_generator = image_generator
        self.style_validator = style_validator or StyleComplianceAgent()
        self.output_manager = output_manager or OutputManager()
        self.sketch_interpreter = sketch_interpreter or SketchInterpreterAgent()

    def _get_image_generator(self) -> ImageGenerationAgent:
        """Instantiate the provider agent lazily for testability."""
        if self.image_generator is None:
            self.image_generator = ImageGenerationAgent()
        return self.image_generator

    def run_sketch_generation(
        self,
        sketch_path: str,
        style: str,
        mode: GenerationMode | str,
        orientation: Orientation,
        model: str | None,
        disable_ai_refinement: bool,
        style_name: str | None = "Default",
        progress_callback: callable = None,
        input_image_bytes: bytes | None = None,
    ) -> dict:
        """Execute the sketch-mode generation pipeline end to end."""
        if progress_callback:
            progress_callback("brief")
        normalized_mode = mode if isinstance(mode, GenerationMode) else GenerationMode(mode)
        request = GenerationRequest(
            input_type="sketch",
            sketch_path=sketch_path,
            style_guidance=style,
            mode=normalized_mode,
            orientation=orientation,
            model_id=model,
            refine_sketch=not disable_ai_refinement,
            selected_style=style_name or "Default",
        )
        output_dir = OutputManager.create_output_directory(Path(sketch_path).stem)
        interpretation = self.sketch_interpreter.interpret(request, output_dir)
        brief = self.brief_agent.create_from_sketch(request, interpretation)
        
        if progress_callback:
            progress_callback("prompt")
        prompt_package = self.prompt_engineer.build_prompt_package(brief)
        import inspect
        sig = inspect.signature(self._complete_generation)
        if "output_dir" in sig.parameters or "progress_callback" in sig.parameters:
            return self._complete_generation(
                request,
                brief,
                prompt_package,
                interpretation,
                output_dir=output_dir,
                progress_callback=progress_callback,
                input_image_bytes=input_image_bytes
            )
        else:
            return self._complete_generation(request, brief, prompt_package, interpretation)

    def _complete_generation(self, request, brief, prompt_package, interpretation, output_dir=None, progress_callback=None, input_image_bytes=None) -> dict:
        """Finish provider generation and artifact persistence for sketch mode."""
        # generate -> validate -> refine -> regenerate loop
        from scenografia.tools.style_validator import StyleValidator
        max_attempts = 3
        response = None
        for attempt in range(max_attempts):
            style_valid, style_issues = StyleValidator.validate_style_contract(prompt_package["final_prompt"])
            neg_valid, neg_issues = StyleValidator.validate_negative_constraints(prompt_package["negative_prompt"])
            issues = [*style_issues, *neg_issues]
            
            if issues:
                if progress_callback:
                    progress_callback("refine")
                if hasattr(self.prompt_engineer, "refine_prompt_package"):
                    prompt_package = self.prompt_engineer.refine_prompt_package(prompt_package, issues)
            
            try:
                if progress_callback:
                    progress_callback("generate")
                generator = self._get_image_generator()
                import inspect
                sig = inspect.signature(generator.generate)
                if "input_image_bytes" in sig.parameters:
                    response = generator.generate(request, prompt_package, brief, input_image_bytes=input_image_bytes)
                else:
                    response = generator.generate(request, prompt_package, brief)
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                if hasattr(self.prompt_engineer, "refine_prompt_package"):
                    prompt_package = self.prompt_engineer.refine_prompt_package(prompt_package, [f"Error: {str(e)}"])

        if progress_callback:
            progress_callback("validate")
        validation_report = self.style_validator.validate_text_run(brief, prompt_package, response)
        metadata = GenerationMetadata(
            run_id=response.request_id,
            input_type="sketch",
            original_prompt=request.style_guidance or request.sketch_path or "sketch input",
            orientation=request.orientation,
            generation_mode=request.mode,
            model_id=response.model_used,
            brief=brief,
            final_prompt=prompt_package["final_prompt"],
            negative_prompt=prompt_package["negative_prompt"],
            image_url=response.image_url,
        )
        if progress_callback:
            progress_callback("persist")
        result = self.output_manager.persist_text_run(
            brief=brief,
            prompt_package=prompt_package,
            response=response,
            validation_report=validation_report,
            metadata=metadata,
            output_dir=output_dir,
            processed_sketch_path=Path(interpretation.processed_sketch_path),
        )
        result["processed_sketch_path"] = Path(interpretation.processed_sketch_path)
        return result