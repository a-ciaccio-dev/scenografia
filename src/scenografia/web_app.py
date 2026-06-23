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
    prompt: str, mode: str, orientation: str, model: Optional[str] = None, style: Optional[str] = "Default", progress_callback: Optional[callable] = None, input_image_bytes: Optional[bytes] = None
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
        progress_callback: Optional progress callback function
        input_image_bytes: Optional bytes of previous image for image-to-image
        
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
            progress_callback=progress_callback,
            input_image_bytes=input_image_bytes,
        )
        logger.info(f"Text generation completata con successo. Risultati in: {result.get('output_dir')}")
        return result
    except Exception as e:
        logger.error(f"Errore durante run_text_generation: {str(e)}", exc_info=True)
        raise e


def run_sketch_generation(
    sketch_path: str, style: str, mode: str, orientation: str, model: Optional[str] = None, style_name: Optional[str] = "Default", progress_callback: Optional[callable] = None, input_image_bytes: Optional[bytes] = None
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
        progress_callback: Optional progress callback function
        input_image_bytes: Optional bytes of previous image for image-to-image
        
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
            progress_callback=progress_callback,
            input_image_bytes=input_image_bytes,
        )
        logger.info(f"Sketch generation completata con successo. Risultati in: {result.get('output_dir')}")
        return result
    except Exception as e:
        logger.error(f"Errore durante run_sketch_generation: {str(e)}", exc_info=True)
        raise e


def on_regenerate(output_dir, image_path_obj, sketch_path, original_prompt, orientation_val, input_type, selected_style, new_mode_key, additions_key):
    """Callback per il tasto di rigenerazione: unisce il prompt originale con le modifiche e avvia la generazione."""
    import streamlit as st
    
    selected_new_mode = st.session_state.get(new_mode_key, "standard")
    prompt_additions = st.session_state.get(additions_key, "")
    
    # Costruisci prompt combinato
    combined_prompt = original_prompt
    if prompt_additions.strip():
        if combined_prompt.endswith(".") or combined_prompt.endswith("!") or combined_prompt.endswith("?"):
            combined_prompt = f"{combined_prompt} {prompt_additions.strip()}"
        else:
            combined_prompt = f"{combined_prompt}. {prompt_additions.strip()}"
            
    # Aggiorna i campi di input nella session_state
    st.session_state.prompt_val = combined_prompt
    st.session_state.text_prompt_input = combined_prompt
    st.session_state.sketch_style = combined_prompt
    
    try:
        # Leggi l'immagine precedente come bytes per image-to-image
        with open(image_path_obj, "rb") as img_file:
            prev_image_bytes = img_file.read()
        
        if input_type == "sketch":
            run_sketch = sketch_path if sketch_path else str(image_path_obj.parent / "processed_sketch.png")
            result = run_sketch_generation(
                sketch_path=str(run_sketch),
                style=combined_prompt,
                mode=selected_new_mode,
                orientation=orientation_val,
                model=None,
                style_name=selected_style,
                input_image_bytes=prev_image_bytes
            )
            st.session_state.active_generation = {
                "output_dir": result.get("output_dir"),
                "image_path": result.get("image_path"),
                "prompt_path": result.get("prompt_path"),
                "sketch_path": result.get("processed_sketch_path")
            }
        else:
            result = run_text_generation(
                prompt=combined_prompt,
                mode=selected_new_mode,
                orientation=orientation_val,
                model=None,
                style=selected_style,
                input_image_bytes=prev_image_bytes
            )
            st.session_state.active_generation = {
                "output_dir": result.get("output_dir"),
                "image_path": result.get("image_path"),
                "prompt_path": result.get("prompt_path"),
                "sketch_path": None
            }
        st.session_state.regen_success = "✅ Generazione completata con nuovo modello!"
    except Exception as e:
        logger.error(f"Errore nella rigenerazione: {str(e)}", exc_info=True)
        st.session_state.regen_error = f"❌ Errore nella rigenerazione: {str(e)}"


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
        if "regen_success" in st.session_state and st.session_state.regen_success:
            st.success(st.session_state.regen_success)
            del st.session_state.regen_success
        if "regen_error" in st.session_state and st.session_state.regen_error:
            st.error(st.session_state.regen_error)
            del st.session_state.regen_error

        if image_path:
            image_path_obj = Path(image_path)
            if image_path_obj.exists():
                st.image(str(image_path_obj), use_container_width=True)
                
                # Load metadata
                import json
                used_mode = "standard"
                original_prompt = ""
                orientation_val = "landscape"
                input_type = "text"
                selected_style = "Default"
                
                metadata_path = Path(output_dir) / "generation_response.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            meta_data = json.load(f)
                            used_mode = meta_data.get("generation_mode", "standard")
                            original_prompt = meta_data.get("original_prompt", "")
                            raw_orientation = meta_data.get("orientation", "landscape")
                            orientation_val = raw_orientation.value if hasattr(raw_orientation, "value") else str(raw_orientation)
                            input_type = meta_data.get("input_type", "text")
                            selected_style = meta_data.get("style_name", "Default")
                    except Exception:
                        pass
                
                all_modes = ["draft", "standard", "production", "vector-ready"]
                default_idx = all_modes.index(used_mode) if used_mode in all_modes else 1
                
                col_dl, col_sel, col_mod, col_go = st.columns([2, 2, 5, 1])
                with col_dl:
                    with open(image_path_obj, "rb") as f:
                        st.download_button(
                            label="⬇️ Scarica immagine",
                            data=f.read(),
                            file_name=image_path_obj.name,
                            mime="image/png"
                        )
                
                with col_sel:
                    selected_new_mode = st.selectbox(
                        "Rigenera con modalità:",
                        options=all_modes,
                        index=default_idx,
                        label_visibility="collapsed",
                        key=f"select_new_mode_{output_dir}"
                    )
                    
                with col_mod:
                    prompt_additions = st.text_input(
                        "Modifiche al prompt",
                        placeholder="Cose da aggiungere al prompt...",
                        label_visibility="collapsed",
                        key=f"prompt_additions_{output_dir}"
                    )
                    
                with col_go:
                    st.button(
                        "GO",
                        key=f"btn_go_{output_dir}",
                        on_click=on_regenerate,
                        args=(
                            output_dir,
                            image_path_obj,
                            sketch_path,
                            original_prompt,
                            orientation_val,
                            input_type,
                            selected_style,
                            f"select_new_mode_{output_dir}",
                            f"prompt_additions_{output_dir}"
                        )
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
    
    # Initialize prompt values in session state
    if "prompt_val" not in st.session_state:
        st.session_state.prompt_val = ""
    if "enhanced_prompt" not in st.session_state:
        st.session_state.enhanced_prompt = None
    if "active_generation" not in st.session_state:
        st.session_state.active_generation = None

    # Load user styles
    from scenografia.styles.loader import load_styles, save_style
    styles_list = load_styles()
    style_names = [s["name"] for s in styles_list]

    # Inject Custom CSS for Premium Look
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif !important;
        }
        
        .main-title {
            font-size: 3rem !important;
            font-weight: 700 !important;
            background: linear-gradient(90deg, #64dfdf, #48cae4, #0077b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem !important;
        }
        
        .stButton button {
            background-color: #0077b6 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        .stButton button:hover {
            background-color: #0096c7 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Container styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            transition: all 0.3s ease;
        }
        
        /* Custom progress logs layout */
        .progress-box {
            background-color: #12131a;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #2d3142;
            margin: 10px 0;
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

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
        model_override = None
        
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
    
    # Step-by-step progress update callback helper
    def update_progress(step):
        steps = {
            "brief": "🔄 [1/5] Normalizzazione del brief scenografico...",
            "prompt": "🔄 [2/5] Elaborazione dello stile e dei vincoli...",
            "refine": "🔄 [3/5] Ottimizzazione e autoverifica del prompt...",
            "generate": "🔄 [4/5] Chiamata alle API di OpenRouter (Generazione)...",
            "validate": "🔄 [5/5] Validazione di conformità finale...",
            "persist": "💾 [✓] Salvataggio degli artefatti in corso..."
        }
        msg = steps.get(step, "🔄 Elaborazione in corso...")
        status_placeholder.markdown(
            f"""
            <div class="progress-box">
                <span style="color: #64dfdf; font-weight: bold;">Status Pipeline:</span> {msg}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ========================
    # TAB 1: Text Prompt
    # ========================
    with tab_text:
        st.subheader("Genera da prompt testuale")
        
        prompt = st.text_area(
            "Descrizione scenografica",
            value=st.session_state.prompt_val,
            placeholder="Es: A mystical forest with ancient stone pillars and magical lights...",
            height=120,
            key="text_prompt_input"
        )
        # Keep session state updated with manual input changes
        st.session_state.prompt_val = prompt
        
        # AI Prompt Enhancer Action
        col_enh_1, col_enh_2 = st.columns([1, 1])
        with col_enh_1:
            if st.button("✨ Migliora con AI Assistant", key="btn_enhance"):
                if not prompt.strip():
                    st.warning("⚠️ Inserisci prima una descrizione di base da migliorare.")
                else:
                    with st.spinner("L'assistente AI sta arricchendo la scena..."):
                        try:
                            from scenografia.agents.prompt_enhancer_agent import PromptEnhancerAgent
                            enhancer = PromptEnhancerAgent()
                            enhanced = enhancer.enhance_prompt(prompt, model_id=model_override if model_override else None)
                            st.session_state.enhanced_prompt = enhanced
                        except Exception as e:
                            st.error(f"Errore: {str(e)}")
                            
        # If enhanced prompt exists, show proposal box
        if st.session_state.enhanced_prompt:
            st.markdown(
                f"""
                <div style="background-color: #1a1c23; border-radius: 10px; padding: 15px; border: 1px solid #3b3f54; margin: 10px 0;">
                    <div style="color: #64dfdf; font-weight: bold; font-size: 15px; margin-bottom: 8px;">✨ Proposta dell'Assistente AI:</div>
                    <div style="color: #d1d5db; font-style: italic; font-size: 14px; line-height: 1.5;">"{st.session_state.enhanced_prompt}"</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            def approve_callback():
                st.session_state.text_prompt_input = st.session_state.enhanced_prompt
                st.session_state.prompt_val = st.session_state.enhanced_prompt
                st.session_state.enhanced_prompt = None

            def reject_callback():
                st.session_state.enhanced_prompt = None

            col_acc, col_rej = st.columns(2)
            with col_acc:
                st.button("✅ Approva e Applica", key="btn_approve_enhanced", on_click=approve_callback)
            with col_rej:
                st.button("❌ Rifiuta", key="btn_reject_enhanced", on_click=reject_callback)

        # Composed Prompt Live Preview
        from scenografia.styles.loader import load_style_by_name
        style_obj = load_style_by_name(selected_style_name)
        style_additions = style_obj.get("prompt_additions", "")
        preview_prompt = f"{BASE_PROMPT}\n{style_additions}\n{prompt}"
        
        with st.expander("🔍 Anteprima Live del Prompt Finale", expanded=False):
            st.text_area("Prompt finale composto (sola lettura)", preview_prompt, height=180, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            generate_button = st.button("🚀 Genera scenografia", key="generate_text")
        
        if generate_button:
            if not prompt.strip():
                st.warning("⚠️ Inserisci un prompt")
            else:
                try:
                    status_placeholder = st.empty()
                    with st.spinner("Pipeline attiva..."):
                        result = run_text_generation(
                            prompt=prompt,
                            mode=mode,
                            orientation=orientation,
                            model=model_override if model_override else None,
                            style=selected_style_name,
                            progress_callback=update_progress
                        )
                    status_placeholder.empty()
                    st.success("✅ Generazione completata!")
                    
                    output_dir = result.get("output_dir")
                    image_path = result.get("image_path")
                    prompt_path = result.get("prompt_path")
                    
                    st.session_state.active_generation = {
                        "output_dir": output_dir,
                        "image_path": image_path,
                        "prompt_path": prompt_path,
                        "sketch_path": None
                    }
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Errore nella generazione: {str(e)}")
                    
        # Display results if there is active generation for text modality
        if st.session_state.active_generation and st.session_state.active_generation.get("sketch_path") is None:
            display_generation_results(**st.session_state.active_generation)
    
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
                    status_placeholder = st.empty()
                    with st.spinner("Processing sketch e generazione..."):
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
                            style_name=selected_style_name,
                            progress_callback=update_progress
                        )
                    status_placeholder.empty()
                    st.success("✅ Generazione completata!")
                    
                    output_dir = result.get("output_dir")
                    image_path = result.get("image_path")
                    prompt_path = result.get("prompt_path")
                    processed_sketch_path = result.get("processed_sketch_path")
                    
                    st.session_state.active_generation = {
                        "output_dir": output_dir,
                        "image_path": image_path,
                        "prompt_path": prompt_path,
                        "sketch_path": processed_sketch_path
                    }
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Errore nella generazione: {str(e)}")
                    
        # Display results if there is active generation for sketch modality
        if st.session_state.active_generation and st.session_state.active_generation.get("sketch_path") is not None:
            display_generation_results(**st.session_state.active_generation)
    
    # ========================
    # Gallery Grid: Recent Runs
    # ========================
    st.divider()
    st.subheader("📚 Galleria Scenografica (Run Recenti)")
    output_dir = Path("output")
    recent_runs = list_recent_runs(output_dir, n=9)
    
    if not recent_runs:
        st.info("Nessun run trovato ancora.")
    else:
        # Show recent runs in a neat 3-column responsive grid
        cols = st.columns(3)
        for idx, run_path in enumerate(recent_runs):
            col = cols[idx % 3]
            with col:
                with st.container(border=True):
                    final_image = find_final_image(run_path)
                    if final_image:
                        st.image(str(final_image), use_container_width=True)
                    
                    st.markdown(f"**{run_path.name[:25]}...**")
                    
                    report = read_validation_report(run_path)
                    if report:
                        val = report.get("orientation_valid", False)
                        style_val = report.get("style_contract_applied", False)
                        status_badge = "🟢 Conforme" if (val and style_val) else "🟡 Avviso"
                        st.caption(f"{status_badge} | {report.get('orientation', 'N/A')}")


if __name__ == "__main__":
    main()
