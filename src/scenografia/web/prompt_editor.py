"""
Prompt editor component for Scenografia Web App.
Renders text prompt area, reference image uploader, AI enhancer controls, and live prompt preview.
"""

from __future__ import annotations

from typing import Any, Optional
import streamlit as st

from scenografia.agents.prompt_enhancer_agent import PromptEnhancerAgent
from scenografia.styles.loader import load_style_by_name
from scenografia.tools.prompt_templates import BASE_PROMPT


def render_text_mode_inputs(
    division: str,
    selected_style_name: str,
    model_override: Optional[str] = None,
) -> dict[str, Any]:
    """
    Render text prompt inputs, enhancer controls, live preview, and the generate trigger button.

    Args:
        division: Scenic division setting (e.g. "Nessuna", "2 parti", ...)
        selected_style_name: Name of selected user style
        model_override: Optional model override identifier

    Returns:
        dict with:
            - generate_clicked: bool
            - prompt: str
            - ref_image_bytes: Optional[bytes]
            - use_as_layout: bool
    """
    st.subheader("Genera da prompt testuale")

    prompt = st.text_area(
        "Descrizione scenografica",
        value=st.session_state.get("prompt_val", ""),
        placeholder="Es: A mystical forest with ancient stone pillars and magical lights...",
        height=120,
        key="text_prompt_input",
    )
    # Keep session state updated with manual input changes
    st.session_state.prompt_val = prompt

    # AI Prompt Enhancer Action & Reference Image Uploader
    col_enh, col_file = st.columns([1, 1])

    with col_file:
        ref_image = st.file_uploader(
            "Carica immagine di riferimento (opzionale)",
            type=["png", "jpg", "jpeg"],
            key="reference_image_uploader",
            help="Un'immagine usata come riferimento per lo stile dell'AI o il layout fisico del disegno finale.",
        )

    ref_image_bytes = None
    if ref_image is not None:
        ref_image_bytes = ref_image.read()

    with col_enh:
        use_as_layout = st.checkbox("Usa per il layout (Image-to-Image)", value=True, key="ref_use_layout")
        use_as_style = st.checkbox("Analizza stile con AI (Vision)", value=True, key="ref_use_style")

        btn_enhance = st.button("✨ Migliora con AI Assistant", key="btn_enhance")

    if btn_enhance:
        if not prompt.strip():
            st.warning("⚠️ Inserisci prima una descrizione di base da migliorare.")
        else:
            with st.spinner("L'assistente AI sta arricchendo la scena..."):
                try:
                    enhancer = PromptEnhancerAgent()
                    passed_img_bytes = ref_image_bytes if use_as_style else None
                    enhanced = enhancer.enhance_prompt(
                        prompt,
                        model_id=model_override if model_override else None,
                        image_bytes=passed_img_bytes,
                        division=division,
                    )
                    st.session_state.enhanced_prompt = enhanced
                except Exception as e:
                    st.error(f"Errore: {str(e)}")

    # If enhanced prompt exists, show proposal box
    if st.session_state.get("enhanced_prompt"):
        st.markdown(
            f"""
            <div style="background-color: #1a1c23; border-radius: 10px; padding: 15px; border: 1px solid #3b3f54; margin: 10px 0;">
                <div style="color: #64dfdf; font-weight: bold; font-size: 15px; margin-bottom: 8px;">✨ Proposta dell'Assistente AI:</div>
                <div style="color: #d1d5db; font-style: italic; font-size: 14px; line-height: 1.5;">"{st.session_state.enhanced_prompt}"</div>
            </div>
            """,
            unsafe_allow_html=True,
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
    style_obj = load_style_by_name(selected_style_name)
    style_additions = style_obj.get("prompt_additions", "") if style_obj else ""
    preview_prompt = f"{BASE_PROMPT}\n{style_additions}\n{prompt}"

    with st.expander("🔍 Anteprima Live del Prompt Finale", expanded=False):
        st.text_area("Prompt finale composto (sola lettura)", preview_prompt, height=180, disabled=True)

    col1, _ = st.columns(2)
    with col1:
        generate_button = st.button("🚀 Genera scenografia", key="generate_text")

    return {
        "generate_clicked": bool(generate_button),
        "prompt": prompt,
        "ref_image_bytes": ref_image_bytes,
        "use_as_layout": use_as_layout,
    }
