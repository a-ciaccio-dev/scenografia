"""
Streamlit web interface for Scenografia.

A local web UI for generating theatrical scenic designs from text prompts
or sketches. Reuses the existing pipeline agents and services.
"""

from pathlib import Path
from typing import Optional
import logging

# Configure logging to console and a local log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scenografia_app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("scenografia_web")


def load_config() -> tuple[bool, str]:
    """
    Initialize Config safely for web interface.
    
    Returns:
        (success: bool, message: str) - If success is False, message contains error.
        Never returns the actual API key in message.
    """
    try:
        from scenografia.config import Config
        Config.initialize()
        logger.info("Configurazione caricata con successo.")
        return (True, "")
    except KeyError as e:
        logger.error(f"Errore caricamento configurazione (KeyError): {str(e)}")
        return (False, "Configura OPENROUTER_API_KEY nel file .env")
    except ValueError as e:
        logger.error(f"Errore caricamento configurazione (ValueError): {str(e)}")
        return (False, f"Errore di configurazione: {str(e)}")
    except Exception as e:
        logger.error(f"Errore caricamento configurazione (Generico): {str(e)}")
        return (False, "Errore nell'inizializzazione: verifica il file .env e le credenziali")


def run_text_generation(
    prompt: str, mode: str, orientation: str, model: Optional[str] = None, style: Optional[str] = "Default"
) -> dict:
    """
    Wrapper for TextGenerationService.run_text_generation().
    
    Called only after button press, never during import.
    
    Args:
        prompt: Text prompt
        mode: GenerationMode value (draft, standard, production, vector-ready)
        orientation: Orientation value (portrait, landscape, square)
        model: Optional model override
        style: Optional style name
        
    Returns:
        Result dict with output_dir, image_path, prompt_path, etc.
    """
    from scenografia.agents.image_generation_agent import TextGenerationService
    from scenografia.schemas.generation_schema import GenerationMode, Orientation
    
    logger.info(f"Avvio text generation. Prompt: '{prompt}' | Mode: {mode} | Orientation: {orientation} | Style: {style}")
    service = TextGenerationService()
    try:
        result = service.run_text_generation(
            prompt=prompt,
            mode=GenerationMode(mode),
            orientation=Orientation(orientation),
            model=model,
            style=style,
        )
        logger.info(f"Text generation completata con successo. Risultati in: {result.get('output_dir')}")
        return result
    except Exception as e:
        logger.error(f"Errore durante run_text_generation: {str(e)}", exc_info=True)
        raise e


def run_sketch_generation(
    sketch_path: str, style: str, mode: str, orientation: str, model: Optional[str] = None, style_name: Optional[str] = "Default"
) -> dict:
    """
    Wrapper for SketchGenerationService.run_sketch_generation().
    
    Called only after button press, never during import.
    
    Args:
        sketch_path: Path to uploaded sketch file
        style: Style guidance text
        mode: GenerationMode value
        orientation: Orientation value
        model: Optional model override
        style_name: Selected user style name
        
    Returns:
        Result dict with output_dir, image_path, processed_sketch_path, etc.
    """
    from scenografia.agents.image_generation_agent import SketchGenerationService
    from scenografia.schemas.generation_schema import GenerationMode, Orientation
    
    logger.info(f"Avvio sketch generation. Sketch: {sketch_path} | Guidance: '{style}' | Mode: {mode} | Orientation: {orientation} | Style Name: {style_name}")
    service = SketchGenerationService()
    try:
        result = service.run_sketch_generation(
            sketch_path=sketch_path,
            style=style,
            mode=GenerationMode(mode),
            orientation=Orientation(orientation),
            model=model,
            disable_ai_refinement=False,
            style_name=style_name,
        )
        logger.info(f"Sketch generation completata con successo. Risultati in: {result.get('output_dir')}")
        return result
    except Exception as e:
        logger.error(f"Errore durante run_sketch_generation: {str(e)}", exc_info=True)
        raise e


def display_generation_results(
    output_dir: str | Path,
    image_path: Optional[str | Path],
    prompt_path: Optional[str | Path],
    sketch_path: Optional[str | Path] = None
) -> None:
    """
    Display generation results in tabs.
    
    Args:
        output_dir: Path to output run directory
        image_path: Path to final.png or None
        prompt_path: Path to prompt.txt or run directory or None
        sketch_path: Optional path to processed_sketch.png
    """
    import streamlit as st
    from scenografia.web_helpers import (
        read_validation_report,
        find_final_image,
        read_prompt_file,
    )
    
    st.subheader("📊 Risultati")
    
    result_tab_image, result_tab_prompt, result_tab_report = st.tabs(
        ["🖼️ Immagine", "📝 Prompt", "✅ Validazione"]
    )
    
    # Image tab
    with result_tab_image:
        if image_path:
            image_path_obj = Path(image_path)
            if image_path_obj.exists():
                st.image(str(image_path_obj), use_container_width=True)
                with open(image_path_obj, "rb") as f:
                    st.download_button(
                        label="⬇️ Scarica immagine",
                        data=f.read(),
                        file_name=image_path_obj.name,
                        mime="image/png"
                    )
            else:
                st.warning("Immagine finale non trovata")
        else:
            st.warning("Immagine finale non trovata")
        
        # Show processed sketch if available (sketch mode)
        if sketch_path:
            sketch_path_obj = Path(sketch_path)
            if sketch_path_obj.exists():
                st.markdown("---")
                st.markdown("#### Sketch processato")
                st.image(str(sketch_path_obj), use_container_width=False, width=300)
    
    # Prompt tab
    with result_tab_prompt:
        prompt_text = None
        if prompt_path:
            prompt_text = read_prompt_file(prompt_path)
        
        if prompt_text:
            st.text_area("Final Prompt", value=prompt_text, height=200, disabled=True)
        else:
            st.info("Prompt file not found")
        
        st.caption(f"Output directory: `{output_dir}`")
    
    # Validation report tab
    with result_tab_report:
        report = read_validation_report(output_dir)
        if report:
            st.json(report)
        else:
            st.info("Validation report not found")


def main():
    """Main Streamlit application."""
    import streamlit as st
    from scenografia.web_helpers import (
        list_recent_runs,
        read_validation_report,
        find_final_image,
        save_uploaded_sketch,
    )
    
    st.set_page_config(page_title="Scenografia", layout="wide")
    st.title("🎭 Scenografia")
    st.markdown("AI-powered theatrical scenic design generation from text or sketch")
    
    # Initialize config on first load
    if "config_ok" not in st.session_state:
        config_ok, config_msg = load_config()
        st.session_state.config_ok = config_ok
        st.session_state.config_msg = config_msg
    
    if not st.session_state.config_ok:
        st.error(f"❌ {st.session_state.config_msg}")
        return
    
    # Load user styles
    from scenografia.styles.loader import load_styles, save_style
    styles_list = load_styles()
    style_names = [s["name"] for s in styles_list]

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configurazione")
        mode = st.selectbox(
            "Generation Mode",
            options=["draft", "standard", "production", "vector-ready"],
            index=1,
            help="Quality/complexity level: draft (fastest) to vector-ready (highest quality)"
        )
        orientation = st.selectbox(
            "Output Orientation",
            options=["landscape", "portrait", "square"],
            index=0,
            help="Canvas proportions"
        )
        model_override = st.text_input(
            "Model Override (optional)",
            value="",
            help="Leave empty to use configured default model"
        )
        
        # User Style Selector
        selected_style_name = st.selectbox(
            "Stile di Disegno",
            options=style_names,
            index=style_names.index("Default") if "Default" in style_names else 0,
            help="Scegli lo stile artistico da sovrapporre al core prompt."
        )

        # Read-only BASE_PROMPT display
        from scenografia.tools.prompt_templates import BASE_PROMPT, BASE_NEGATIVE
        with st.expander("Prompt base SVG-safe"):
            st.text_area("BASE_PROMPT (sola lettura)", BASE_PROMPT, height=200, disabled=True)
            st.text_area("BASE_NEGATIVE (sola lettura)", BASE_NEGATIVE, height=100, disabled=True)

        # Style creator form
        with st.expander("🎨 Crea Nuovo Stile"):
            new_style_name = st.text_input("Nome stile", key="new_style_name")
            new_style_desc = st.text_input("Descrizione", key="new_style_desc")
            new_style_prompt = st.text_area("Prompt aggiuntivo", key="new_style_prompt")
            new_style_neg = st.text_area("Negative prompt aggiuntivo", key="new_style_neg")
            
            if st.button("Salva stile", key="save_style_button"):
                if not new_style_name.strip():
                    st.error("Il nome dello stile non può essere vuoto.")
                else:
                    try:
                        save_style({
                            "name": new_style_name.strip(),
                            "description": new_style_desc.strip(),
                            "prompt_additions": new_style_prompt.strip(),
                            "negative_additions": new_style_neg.strip()
                        })
                        st.success(f"Stile '{new_style_name}' salvato!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {str(e)}")
    
    # Main content: tabs for workflow selection
    tab_text, tab_sketch = st.tabs(["📝 Da Prompt", "🎨 Da Sketch"])
    
    # ========================
    # TAB 1: Text Prompt
    # ========================
    with tab_text:
        st.subheader("Genera da prompt testuale")
        
        prompt = st.text_area(
            "Descrizione scenografica",
            placeholder="Es: A mystical forest with ancient stone pillars and magical lights...",
            height=120,
            key="text_prompt"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            generate_button = st.button("🚀 Genera scenografia", key="generate_text")
        
        if generate_button:
            if not prompt.strip():
                st.warning("⚠️ Inserisci un prompt")
            else:
                try:
                    with st.spinner("Generazione in corso..."):
                        result = run_text_generation(
                            prompt=prompt,
                            mode=mode,
                            orientation=orientation,
                            model=model_override if model_override else None,
                            style=selected_style_name
                        )
                    
                    # Display results
                    st.success("✅ Generazione completata!")
                    
                    output_dir = result.get("output_dir")
                    image_path = result.get("image_path")
                    prompt_path = result.get("prompt_path")
                    
                    display_generation_results(
                        output_dir=output_dir,
                        image_path=image_path,
                        prompt_path=prompt_path,
                        sketch_path=None
                    )
                    
                except Exception as e:
                    st.error(f"❌ Errore nella generazione: {str(e)}")
    
    # ========================
    # TAB 2: Sketch Upload
    # ========================
    with tab_sketch:
        st.subheader("Genera da sketch")
        
        sketch_file = st.file_uploader(
            "Carica uno sketch (PNG o JPG)",
            type=["png", "jpg", "jpeg"],
            key="sketch_upload"
        )
        
        style = st.text_area(
            "Stile e indicazioni",
            placeholder="Es: fairytale theatrical backdrop, full color, hand-drawn style...",
            height=100,
            key="sketch_style"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            generate_sketch_button = st.button("🚀 Genera da sketch", key="generate_sketch")
        
        if generate_sketch_button:
            if sketch_file is None:
                st.warning("⚠️ Carica uno sketch")
            elif not style.strip():
                st.warning("⚠️ Inserisci indicazioni di stile")
            else:
                try:
                    with st.spinner("Processing sketch e generazione in corso..."):
                        # Save uploaded sketch
                        sketches_dir = Path("input/sketches")
                        sketch_path = save_uploaded_sketch(
                            uploaded_file_bytes=sketch_file.read(),
                            filename=sketch_file.name,
                            sketches_dir=sketches_dir
                        )
                        
                        # Generate
                        result = run_sketch_generation(
                            sketch_path=str(sketch_path),
                            style=style,
                            mode=mode,
                            orientation=orientation,
                            model=model_override if model_override else None,
                            style_name=selected_style_name
                        )
                    
                    st.success("✅ Generazione completata!")
                    
                    output_dir = result.get("output_dir")
                    image_path = result.get("image_path")
                    prompt_path = result.get("prompt_path")
                    processed_sketch_path = result.get("processed_sketch_path")
                    
                    display_generation_results(
                        output_dir=output_dir,
                        image_path=image_path,
                        prompt_path=prompt_path,
                        sketch_path=processed_sketch_path
                    )
                    
                except Exception as e:
                    st.error(f"❌ Errore nella generazione: {str(e)}")
    
    # ========================
    # Gallery: Recent Runs
    # ========================
    st.divider()
    with st.expander("📚 Run recenti", expanded=False):
        output_dir = Path("output")
        recent_runs = list_recent_runs(output_dir, n=5)
        
        if not recent_runs:
            st.info("Nessun run trovato ancora.")
        else:
            for run_path in recent_runs:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(run_path.name)
                        
                        # Show validation report if available
                        report = read_validation_report(run_path)
                        if report:
                            orientation_val = report.get("orientation", "N/A")
                            valid = report.get("orientation_valid", False)
                            status = "✅ Valido" if valid else "⚠️ Non valido"
                            st.caption(f"{status} | Orientation: {orientation_val}")
                    
                    with col2:
                        # Show final.png thumbnail if available
                        final_image = find_final_image(run_path)
                        if final_image:
                            st.image(str(final_image), width=150)


if __name__ == "__main__":
    main()
