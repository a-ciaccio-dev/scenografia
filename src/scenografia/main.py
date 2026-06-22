"""CLI entry point for Scenografia."""

from pathlib import Path
from typing import Optional
import json

import typer

from scenografia.agents.image_generation_agent import SketchGenerationService, TextGenerationService
from scenografia.agents.style_compliance_agent import StyleComplianceAgent
from scenografia.config import Config
from scenografia.tools.output_manager import OutputManager
from scenografia.schemas.generation_schema import GenerationMode, Orientation


app = typer.Typer()


def _parse_orientation(value: str) -> Orientation:
    """Parse and validate an orientation string."""
    normalized = value.strip().lower()
    try:
        return Orientation(normalized)
    except ValueError as exc:
        typer.echo("Invalid orientation. Choose one of: portrait, landscape, square.")
        raise typer.Exit(code=2) from exc


def _resolve_orientation(orientation: Optional[str]) -> Orientation:
    """Resolve orientation from CLI option or interactive prompt."""
    if orientation is not None:
        return _parse_orientation(orientation)

    selected = typer.prompt("Orientation (portrait, landscape, square)")
    return _parse_orientation(selected)


@app.command()
def generate(
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Text prompt input mode."),
    sketch: Optional[str] = typer.Option(None, "--sketch", help="Sketch input mode."),
    style: Optional[str] = typer.Option(None, "--style", help="Style guidance for sketch mode."),
    mode: GenerationMode = typer.Option(..., "--mode", help="Generation mode."),
    orientation: Optional[str] = typer.Option(None, "--orientation", help="Output orientation."),
    model: Optional[str] = typer.Option(None, "--model", help="Optional model override."),
    disable_ai_refinement: bool = typer.Option(False, "--disable-ai-refinement", help="Disable optional AI refinement for sketch mode."),
) -> None:
    """Generate a scenic design from text or sketch."""
    if bool(prompt) == bool(sketch):
        raise typer.BadParameter("Provide exactly one of --prompt or --sketch.")

    resolved_orientation = _resolve_orientation(orientation)

    if prompt:
        style_name = style if style else "Default"
        service = TextGenerationService()
        
        import inspect
        sig = inspect.signature(service.run_text_generation)
        kwargs = {
            "prompt": prompt,
            "mode": mode,
            "orientation": resolved_orientation,
            "model": model,
        }
        if "style" in sig.parameters:
            kwargs["style"] = style_name
            
        result = service.run_text_generation(**kwargs)
        output_dir = Path(result["output_dir"]).as_posix()
        typer.echo(f"Generated scenic design in {output_dir}")
        return

    if not style:
        typer.echo("Style guidance is required when using --sketch.")
        raise typer.Exit(code=2)

    from scenografia.styles.loader import load_style_by_name, load_styles
    known_styles = [s.get("name", "").lower() for s in load_styles()]
    
    if style.strip().lower() in known_styles:
        style_name = style.strip()
        style_obj = load_style_by_name(style_name)
        style_guidance = style_obj.get("description", style_name)
    else:
        style_name = "Default"
        style_guidance = style

    service = SketchGenerationService()
    
    import inspect
    sig = inspect.signature(service.run_sketch_generation)
    kwargs = {
        "sketch_path": sketch,
        "style": style_guidance,
        "mode": mode,
        "orientation": resolved_orientation,
        "model": model,
        "disable_ai_refinement": disable_ai_refinement,
    }
    if "style_name" in sig.parameters:
        kwargs["style_name"] = style_name
        
    result = service.run_sketch_generation(**kwargs)
    output_dir = Path(result["output_dir"]).as_posix()
    processed_sketch = Path(result["processed_sketch_path"]).as_posix()
    typer.echo(f"Generated scenic design in {output_dir}")
    typer.echo(f"Processed sketch saved to {processed_sketch}")


@app.command()
def validate(
    image: Optional[str] = typer.Option(None, "--image", help="Path to a generated final image."),
    run: Optional[str] = typer.Option(None, "--run", help="Path to a completed run folder."),
) -> None:
    """Validate scenic style compliance and artifact completeness."""
    if bool(image) == bool(run):
        raise typer.BadParameter("Provide exactly one of --image or --run.")

    agent = StyleComplianceAgent()
    if image:
        image_path = Path(image)
        if not image_path.exists():
            typer.echo(f"Image not found: {image_path.as_posix()}")
            raise typer.Exit(code=2)
        report = agent.validate_image_path(image_path)
        run_dir = image_path.parent
    else:
        run_dir = Path(run)
        if not run_dir.exists() or not run_dir.is_dir():
            typer.echo(f"Run folder not found: {run_dir.as_posix()}")
            raise typer.Exit(code=2)
        report = agent.validate_run_folder(run_dir)

    report_path = OutputManager.save_validation_report(run_dir, report)
    typer.echo(f"Validation report saved to {report_path.as_posix()}")
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))

    if report.orientation_valid and report.style_contract_applied and report.negative_constraints_applied and report.artifacts_complete:
        raise typer.Exit(code=0)

    raise typer.Exit(code=1)


@app.command()
def models() -> None:
    """List available models for each generation mode."""
    lines = ["Configured generation models:"]
    for mode in GenerationMode:
        configured_model = Config.get_model_for_mode(mode)
        model_display = configured_model if configured_model else "not configured (set in .env)"
        lines.append(f"- {mode.value}: {model_display}")
    typer.echo("\n".join(lines))


if __name__ == "__main__":
    app()
