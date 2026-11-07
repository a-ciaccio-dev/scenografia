"""
Sidebar settings component for Scenografia Web App.
Renders mode, orientation, style selector, scenic division, BASE_PROMPT viewer, and style creator.
"""

from __future__ import annotations

from typing import Any, Optional
import streamlit as st

from scenografia.styles.loader import save_style
from scenografia.tools.prompt_templates import BASE_NEGATIVE, BASE_PROMPT


def render_sidebar_settings(style_names: list[str]) -> dict[str, Any]:
    """
    Render configuration controls in the Streamlit sidebar.

    Args:
        style_names: List of available style names.

    Returns:
        dict containing:
            - mode: Selected generation mode string
            - orientation: Selected output orientation string
            - selected_style_name: Selected style name string
            - division: Selected scenic division string
            - model_override: Optional model override string
    """
    with st.sidebar:
        st.header("⚙️ Configurazione")
        mode = st.selectbox(
            "Generation Mode",
            options=["draft", "standard", "production", "vector-ready"],
            index=1,
            help="Quality/complexity level: draft (fastest) to vector-ready (highest quality)",
        )
        orientation = st.selectbox(
            "Output Orientation",
            options=["landscape", "portrait", "square"],
            index=0,
            help="Canvas proportions",
        )
        model_override: Optional[str] = None

        # User Style Selector
        selected_style_name = st.selectbox(
            "Stile di Disegno",
            options=style_names,
            index=style_names.index("Default") if "Default" in style_names else 0,
            help="Scegli lo stile artistico da sovrapporre al core prompt.",
        )

        # Scenic Division Selector
        division = st.selectbox(
            "Divisione Scenica",
            options=["Nessuna", "2 parti", "3 parti", "4 parti"],
            index=0,
            help="Suddividi il disegno in più pannelli o parti verticali",
        )

        # SVG Export Option
        export_svg = st.checkbox(
            "Esporta SVG Vettoriale",
            value=False,
            help="Genera automaticamente un file SVG vettoriale scalabile insieme al PNG.",
        )

        # Read-only BASE_PROMPT display
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
                            "negative_additions": new_style_neg.strip(),
                        })
                        st.success(f"Stile '{new_style_name}' salvato!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {str(e)}")

    return {
        "mode": mode,
        "orientation": orientation,
        "selected_style_name": selected_style_name,
        "division": division,
        "export_svg": export_svg,
        "model_override": model_override,
    }
