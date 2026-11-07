"""
Results view component for Scenografia Web App.
Renders tabs for generated image, prompt, and validation report, along with regeneration controls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from scenografia.logger import setup_logger

logger = setup_logger("scenografia_results_view")
from scenografia.web_helpers import (
    find_final_image,
    read_prompt_file,
    read_validation_report,
)


def on_regenerate(
    output_dir: str | Path,
    image_path_obj: Path,
    sketch_path: Optional[str | Path],
    original_prompt: str,
    orientation_val: str,
    input_type: str,
    selected_style: str,
    new_mode_key: str,
    additions_key: str,
) -> None:
    """Callback per il tasto di rigenerazione: unisce il prompt originale con le modifiche e avvia la generazione."""
    import streamlit as st
    from scenografia.services import SketchGenerationService, TextGenerationService
    from scenografia.schemas.generation_schema import GenerationMode, Orientation

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
            service = SketchGenerationService()
            result = service.run_sketch_generation(
                sketch_path=str(run_sketch),
                style=combined_prompt,
                mode=GenerationMode(selected_new_mode),
                orientation=Orientation(orientation_val),
                model=None,
                disable_ai_refinement=False,
                style_name=selected_style,
                input_image_bytes=prev_image_bytes,
            )
            st.session_state.active_generation = {
                "output_dir": result.get("output_dir"),
                "image_path": result.get("image_path"),
                "prompt_path": result.get("prompt_path"),
                "sketch_path": result.get("processed_sketch_path"),
            }
        else:
            service = TextGenerationService()
            result = service.run_text_generation(
                prompt=combined_prompt,
                mode=GenerationMode(selected_new_mode),
                orientation=Orientation(orientation_val),
                model=None,
                style=selected_style,
                input_image_bytes=prev_image_bytes,
            )
            st.session_state.active_generation = {
                "output_dir": result.get("output_dir"),
                "image_path": result.get("image_path"),
                "prompt_path": result.get("prompt_path"),
                "sketch_path": None,
            }
        st.session_state.regen_success = "✅ Generazione completata con nuovo modello!"
    except Exception as e:
        logger.error(f"Errore nella rigenerazione: {str(e)}", exc_info=True)
        st.session_state.regen_error = f"❌ Errore nella rigenerazione: {str(e)}"


def display_generation_results(
    output_dir: str | Path,
    image_path: Optional[str | Path],
    prompt_path: Optional[str | Path],
    sketch_path: Optional[str | Path] = None,
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
                            mime="image/png",
                        )
                    svg_file = Path(output_dir) / "scene_vector.svg"
                    if svg_file.exists():
                        with open(svg_file, "r", encoding="utf-8") as f_svg:
                            st.download_button(
                                label="📐 Scarica SVG Vettoriale",
                                data=f_svg.read(),
                                file_name=svg_file.name,
                                mime="image/svg+xml",
                                key=f"dl_svg_{output_dir}",
                            )

                with col_sel:
                    selected_new_mode = st.selectbox(
                        "Rigenera con modalità:",
                        options=all_modes,
                        index=default_idx,
                        label_visibility="collapsed",
                        key=f"select_new_mode_{output_dir}",
                    )

                with col_mod:
                    prompt_additions = st.text_input(
                        "Modifiche al prompt",
                        placeholder="Cose da aggiungere al prompt...",
                        label_visibility="collapsed",
                        key=f"prompt_additions_{output_dir}",
                        on_change=on_regenerate,
                        args=(
                            output_dir,
                            image_path_obj,
                            sketch_path,
                            original_prompt,
                            orientation_val,
                            input_type,
                            selected_style,
                            f"select_new_mode_{output_dir}",
                            f"prompt_additions_{output_dir}",
                        ),
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
                            f"prompt_additions_{output_dir}",
                        ),
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
