import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

STYLES_DIR = Path(__file__).parent.resolve()


def _ensure_styles_dir() -> Path:
    """Ensure the styles directory exists and contains at least the default styles."""
    STYLES_DIR.mkdir(parents=True, exist_ok=True)
    return STYLES_DIR


def sanitize_filename(name: str) -> str:
    """Sanitize the style name to be safe for filenames."""
    if not name or not name.strip():
        raise ValueError("Style name cannot be empty")
    # Replace spaces with underscores, remove unsafe chars
    clean = re.sub(r"[^\w\-_]", "", name.strip().replace(" ", "_").lower())
    if not clean:
        clean = "custom_style"
    return f"{clean}.json"


def load_styles() -> List[Dict[str, Any]]:
    """Load all JSON styles from the styles directory."""
    _ensure_styles_dir()
    styles = []
    
    # Standard styles to write if directory is empty or missing them
    default_styles = {
        "default.json": {
            "name": "Default",
            "description": "stile teatrale standard",
            "prompt_additions": "",
            "negative_additions": ""
        },
        "minimal.json": {
            "name": "Minimal",
            "description": "stile scenografico minimalista",
            "prompt_additions": "minimal stage composition, few scenic elements, geometric forms, large empty spaces, simple theatrical composition",
            "negative_additions": "clutter, excessive detail, crowded composition, complex ornaments"
        },
        "espressionista.json": {
            "name": "Espressionista",
            "description": "stile teatrale espressionista",
            "prompt_additions": "expressionist theatrical set design, distorted perspective, dramatic angles, exaggerated shapes, symbolic scenic elements, strong emotional composition",
            "negative_additions": "realistic proportions, naturalistic rendering, photographic realism"
        }
    }

    # If directories are empty of these three, recreate them
    for fname, content in default_styles.items():
        fpath = STYLES_DIR / fname
        if not fpath.exists():
            try:
                fpath.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

    for file_path in STYLES_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "name" in data:
                    styles.append(data)
        except Exception:
            # Skip invalid files silently
            continue
            
    # Always ensure default is in the list
    if not any(s.get("name", "").lower() == "default" for s in styles):
        styles.append(default_styles["default.json"])
        
    return styles


def load_style_by_name(name: str) -> Dict[str, Any]:
    """Load a style by its name, with fallback to default style."""
    styles = load_styles()
    target_name = name.strip().lower()
    
    # Try exact or case-insensitive match
    for style in styles:
        if style.get("name", "").strip().lower() == target_name:
            return style
            
    # Fallback to Default
    for style in styles:
        if style.get("name", "").strip().lower() == "default":
            return style
            
    return {
        "name": "Default",
        "description": "stile teatrale standard",
        "prompt_additions": "",
        "negative_additions": ""
    }


def save_style(style: Dict[str, Any]) -> None:
    """Save a style to a JSON file in the styles directory."""
    _ensure_styles_dir()
    name = style.get("name")
    if not name or not str(name).strip():
        raise ValueError("Style name cannot be empty")
        
    filename = sanitize_filename(str(name))
    
    # Prevent path traversal
    safe_path = (STYLES_DIR / filename).resolve()
    if not safe_path.is_relative_to(STYLES_DIR):
        raise ValueError("Invalid style name or path traversal detected")
        
    # Ensure correct format
    cleaned_style = {
        "name": str(style.get("name", "")),
        "description": str(style.get("description", "")),
        "prompt_additions": str(style.get("prompt_additions", "")),
        "negative_additions": str(style.get("negative_additions", ""))
    }
    
    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_style, f, indent=2, ensure_ascii=False)
