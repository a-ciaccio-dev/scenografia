"""
Streamlit web interface for Scenografia.

A local web UI for generating theatrical scenic designs from text prompts
or sketches. Orchestrates modular components from scenografia.web and services.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from scenografia.logger import setup_logger
from scenografia.web import (
    display_generation_results,
    on_regenerate,
    render_sidebar_settings,
    render_text_mode_inputs,
)

logger = setup_logger("scenografia_web")


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
    prompt: str,
    mode: str,
    orientation: str,
    model: Optional[str] = None,
    style: Optional[str] = "Default",
    progress_callback: Optional[Callable[[str], None]] = None,
    input_image_bytes: Optional[bytes] = None,
    division: Optional[str] = "Nessuna",
) -> dict:
    """
    Wrapper for TextGenerationService.run_text_generation().

    Called only after button press, never during import.
    """
    from scenografia.agents.image_generation_agent import TextGenerationService
    from scenografia.schemas.generation_schema import GenerationMode, Orientation

    # Inject scenic division constraint if requested
    division_instruction = ""
    if division == "2 parti":
        division_instruction = "The composition must be visibly divided into 2 symmetrical sections, separated by a vertical element (such as a column, beam, or vertical feature), acting as a visual and structural boundary."
    elif division == "3 parti":
        division_instruction = "The composition must be visibly divided into 3 equal vertical panels, separated by vertical elements (such as columns, beams, or vertical features), acting as visual and structural boundaries."
    elif division == "4 parti":
        division_instruction = "The composition must be visibly divided into 4 equal vertical panels, separated by vertical elements (such as columns, beams, or vertical features), acting as visual and structural boundaries."

    if division_instruction:
        prompt = f"{prompt}\nComposition layout: {division_instruction}"

    logger.info(f"Avvio text generation. Prompt: '{prompt}' | Mode: {mode} | Orientation: {orientation} | Style: {style} | Division: {division}")
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
    sketch_path: str,
    style: str,
    mode: str,
    orientation: str,
    model: Optional[str] = None,
    style_name: Optional[str] = "Default",
    progress_callback: Optional[Callable[[str], None]] = None,
    input_image_bytes: Optional[bytes] = None,
) -> dict:
    """
    Wrapper for SketchGenerationService.run_sketch_generation().

    Called only after button press, never during import.
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


def main():
    """Main Streamlit application."""
    import streamlit as st
    from scenografia.styles.loader import load_styles
    from scenografia.web_helpers import (
        find_final_image,
        list_recent_runs,
        read_validation_report,
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
        unsafe_allow_html=True,
    )

    # 1. Render Sidebar Settings Component
    sidebar_cfg = render_sidebar_settings(style_names)

    # Step-by-step progress update callback helper
    def update_progress(step: str):
        steps = {
            "brief": "🔄 [1/5] Normalizzazione del brief scenografico...",
            "prompt": "🔄 [2/5] Elaborazione dello stile e dei vincoli...",
            "refine": "🔄 [3/5] Ottimizzazione e autoverifica del prompt...",
            "generate": "🔄 [4/5] Chiamata alle API di OpenRouter (Generazione)...",
            "validate": "🔄 [5/5] Validazione di conformità finale...",
            "persist": "💾 [✓] Salvataggio degli artefatti in corso...",
        }
        msg = steps.get(step, "🔄 Elaborazione in corso...")
        status_placeholder.markdown(
            f"""
            <div class="progress-box">
                <span style="color: #64dfdf; font-weight: bold;">Status Pipeline:</span> {msg}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Render Prompt Editor Component
    editor_state = render_text_mode_inputs(
        division=sidebar_cfg["division"],
        selected_style_name=sidebar_cfg["selected_style_name"],
        model_override=sidebar_cfg["model_override"],
    )

    if editor_state["generate_clicked"]:
        prompt = editor_state["prompt"]
        if not prompt.strip():
            st.warning("⚠️ Inserisci un prompt")
        else:
            try:
                status_placeholder = st.empty()
                with st.spinner("Pipeline attiva..."):
                    passed_layout_bytes = editor_state["ref_image_bytes"] if editor_state["use_as_layout"] else None
                    result = run_text_generation(
                        prompt=prompt,
                        mode=sidebar_cfg["mode"],
                        orientation=sidebar_cfg["orientation"],
                        model=sidebar_cfg["model_override"],
                        style=sidebar_cfg["selected_style_name"],
                        progress_callback=update_progress,
                        input_image_bytes=passed_layout_bytes,
                        division=sidebar_cfg["division"],
                    )
                status_placeholder.empty()
                st.success("✅ Generazione completata!")

                st.session_state.active_generation = {
                    "output_dir": result.get("output_dir"),
                    "image_path": result.get("image_path"),
                    "prompt_path": result.get("prompt_path"),
                    "sketch_path": None,
                }
                st.rerun()

            except Exception as e:
                st.error(f"❌ Errore nella generazione: {str(e)}")

    # 3. Render Results View Component
    if st.session_state.active_generation:
        display_generation_results(**st.session_state.active_generation)

    # 4. Gallery Grid: Recent Runs
    st.divider()
    st.subheader("📚 Galleria Scenografica (Run Recenti)")
    output_dir = Path("output")
    recent_runs = list_recent_runs(output_dir, n=9)

    if not recent_runs:
        st.info("Nessun run trovato ancora.")
    else:
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
