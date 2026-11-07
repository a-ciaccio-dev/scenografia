"""Text-mode theatrical scenic generation service."""

from collections.abc import Callable
from typing import Optional, Dict, Any, Union

from scenografia.agents.brief_agent import BriefAgent
from scenografia.agents.prompt_engineer_agent import PromptEngineerAgent
from scenografia.agents.style_compliance_agent import StyleComplianceAgent
from scenografia.schemas.generation_schema import GenerationMode, GenerationRequest, Orientation
from scenografia.schemas.validation_schema import GenerationMetadata
from scenografia.tools.output_manager import OutputManager
from scenografia.tools.style_validator import StyleValidator


class TextGenerationService:
    """Orchestrate the text-mode generation pipeline end-to-end."""

    def __init__(
        self,
        brief_agent: Optional[BriefAgent] = None,
        prompt_engineer: Optional[PromptEngineerAgent] = None,
        image_generator: Any = None,
        style_validator: Optional[StyleComplianceAgent] = None,
        output_manager: Optional[OutputManager] = None,
    ):
        self.brief_agent = brief_agent or BriefAgent()
        self.prompt_engineer = prompt_engineer or PromptEngineerAgent()
        self.image_generator = image_generator
        self.style_validator = style_validator or StyleComplianceAgent()
        self.output_manager = output_manager or OutputManager()

    def _get_image_generator(self):
        """Instantiate provider agent lazily for testability."""
        if self.image_generator is None:
            from scenografia.agents.image_generation_agent import ImageGenerationAgent
            self.image_generator = ImageGenerationAgent()
        return self.image_generator

    def run_text_generation(
        self,
        prompt: str,
        mode: Union[GenerationMode, str],
        orientation: Orientation,
        model: Optional[str],
        style: Optional[str] = "Default",
        progress_callback: Optional[Callable[[str], None]] = None,
        input_image_bytes: Optional[bytes] = None,
        export_svg: bool = False,
        layer: Optional[str] = "all",
    ) -> Dict[str, Any]:
        """Execute the text-mode generation pipeline end to end."""
        from scenografia.tools.prompt_templates import get_depth_layer_instruction

        if layer and layer.lower() != "all":
            layer_instr = get_depth_layer_instruction(layer)
            if layer_instr:
                prompt = f"{prompt}\nScenic Depth Layer: {layer_instr}"

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
                response = generator.generate(request, prompt_package, brief, input_image_bytes=input_image_bytes)
                break
            except Exception as e:
                err_text = str(e).lower()
                is_fatal = any(term in err_text for term in ["401", "402", "403", "404", "unauthorized", "payment required", "forbidden", "not found", "quota"])
                if is_fatal or attempt == max_attempts - 1:
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
        if progress_callback:
            progress_callback("persist")

        import inspect
        persist_sig = inspect.signature(self.output_manager.persist_text_run)
        persist_kwargs = {
            "brief": brief,
            "prompt_package": prompt_package,
            "response": response,
            "validation_report": validation_report,
            "metadata": metadata,
        }
        if "export_svg" in persist_sig.parameters:
            persist_kwargs["export_svg"] = export_svg
        return self.output_manager.persist_text_run(**persist_kwargs)
