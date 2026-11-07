"""
History gallery component for Scenografia Web App.
Renders historical runs with filters, visual cards, validation badges, and run reload.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import streamlit as st

from scenografia.web_helpers import (
    find_final_image,
    list_recent_runs,
    read_validation_report,
)


def render_history_gallery(
    output_dir: Path | str = "output",
    max_items: int = 12,
) -> None:
    """
    Render recent runs history gallery in a responsive grid with metadata and reload actions.

    Args:
        output_dir: Base directory where run outputs are stored.
        max_items: Maximum number of recent runs to display.
    """
    st.divider()
    st.subheader("📚 Galleria Scenografica (Run Recenti)")

    base_path = Path(output_dir)
    recent_runs = list_recent_runs(base_path, n=max_items)

    if not recent_runs:
        st.info("Nessun run trovato ancora.")
        return

    # Filter controls in columns
    col_filter_style, col_filter_status = st.columns([1, 1])

    # Collect metadata for runs
    runs_meta: list[dict] = []
    available_styles = {"Tutti"}

    for run_path in recent_runs:
        meta_file = run_path / "generation_response.json"
        style_name = "Default"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    style_name = data.get("style_name", "Default")
            except Exception:
                pass
        available_styles.add(style_name)

        report = read_validation_report(run_path)
        is_compliant = False
        orientation = "N/A"
        if report:
            val = report.get("orientation_valid", False)
            style_val = report.get("style_contract_applied", False)
            is_compliant = bool(val and style_val)
            orientation = str(report.get("orientation", "N/A"))

        runs_meta.append({
            "path": run_path,
            "style": style_name,
            "is_compliant": is_compliant,
            "orientation": orientation,
            "final_image": find_final_image(run_path),
        })

    with col_filter_style:
        selected_style_filter = st.selectbox(
            "Filtra per Stile",
            options=sorted(list(available_styles)),
            index=0,
            key="gallery_filter_style",
        )

    with col_filter_status:
        selected_status_filter = st.selectbox(
            "Filtra per Stato",
            options=["Tutti", "Conforme", "Avviso"],
            index=0,
            key="gallery_filter_status",
        )

    # Filter logic
    filtered_runs = [
        r for r in runs_meta
        if (selected_style_filter == "Tutti" or r["style"] == selected_style_filter)
        and (
            selected_status_filter == "Tutti"
            or (selected_status_filter == "Conforme" and r["is_compliant"])
            or (selected_status_filter == "Avviso" and not r["is_compliant"])
        )
    ]

    if not filtered_runs:
        st.caption("Nessun run corrisponde ai filtri selezionati.")
        return

    # Render grid (3 columns)
    cols = st.columns(3)
    for idx, item in enumerate(filtered_runs):
        run_path = item["path"]
        col = cols[idx % 3]
        with col:
            with st.container(border=True):
                if item["final_image"]:
                    st.image(str(item["final_image"]), use_container_width=True)
                else:
                    st.caption("🖼️ Nessuna immagine finale")

                st.markdown(f"**{run_path.name[:24]}...**")
                status_badge = "🟢 Conforme" if item["is_compliant"] else "🟡 Avviso"
                st.caption(f"{status_badge} | {item['orientation']} | {item['style']}")

                # Action buttons
                col_load, col_down = st.columns([1, 1])
                with col_load:
                    if st.button("🔍 Apri", key=f"btn_open_{run_path.name}"):
                        st.session_state.active_generation = {
                            "output_dir": run_path,
                            "image_path": item["final_image"],
                            "prompt_path": run_path / "prompt.txt",
                            "sketch_path": run_path / "processed_sketch.png" if (run_path / "processed_sketch.png").exists() else None,
                        }
                        st.rerun()

                with col_down:
                    if item["final_image"] and item["final_image"].exists():
                        with open(item["final_image"], "rb") as f:
                            st.download_button(
                                label="⬇️ File",
                                data=f.read(),
                                file_name=item["final_image"].name,
                                mime="image/png",
                                key=f"btn_dl_{run_path.name}",
                            )
