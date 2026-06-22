"""
Pure helper functions for Streamlit web interface.

These functions are testable, have no side effects during import,
and handle file I/O and data transformations for the web UI.
"""

import json
import re
from pathlib import Path
from typing import Optional, Any


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize uploaded filename to prevent path traversal and invalid characters.
    
    Args:
        filename: Original filename from upload
        max_length: Maximum allowed filename length
        
    Returns:
        Safe filename suitable for filesystem storage
    """
    # Extract only the filename (remove any path components)
    safe = Path(filename).name
    
    # Replace invalid characters (keep only alphanumeric, dash, underscore, dot)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", safe)
    
    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")
    
    # Truncate if necessary
    if len(safe) > max_length:
        if "." in safe:
            name, ext = safe.rsplit(".", 1)
            max_name_len = max_length - len(ext) - 1
            safe = name[:max_name_len] + "." + ext
        else:
            safe = safe[:max_length]
    
    # Ensure it's not empty
    if not safe or safe == "":
        safe = "upload"
    
    return safe


def list_recent_runs(output_dir: str | Path, n: int = 10) -> list[Path]:
    """
    List most recent generation runs from output directory.
    
    Args:
        output_dir: Path to output directory
        n: Number of recent runs to return
        
    Returns:
        List of Path objects in descending order (newest first)
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        return []
    
    # Find all subdirectories matching run pattern (YYYY-MM-DD_HHMM_*)
    runs = [
        d for d in output_path.iterdir()
        if d.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}_\d{4}_", d.name)
    ]
    
    # Sort by name descending (newest first)
    runs.sort(key=lambda x: x.name, reverse=True)
    
    return runs[:n]


def read_validation_report(run_dir: str | Path) -> Optional[dict[str, Any]]:
    """
    Read validation_report.json from a run directory.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Parsed JSON dict, or None if file doesn't exist or is invalid
    """
    report_path = Path(run_dir) / "validation_report.json"
    
    if not report_path.exists():
        return None
    
    try:
        with open(report_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def find_final_image(run_dir: str | Path) -> Optional[Path]:
    """
    Find final.png in a run directory.
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Path to final.png, or None if not found
    """
    image_path = Path(run_dir) / "final.png"
    return image_path if image_path.exists() else None


def find_processed_sketch(run_dir: str | Path) -> Optional[Path]:
    """
    Find processed_sketch.png in a run directory (sketch mode only).
    
    Args:
        run_dir: Path to run directory
        
    Returns:
        Path to processed_sketch.png, or None if not found
    """
    sketch_path = Path(run_dir) / "processed_sketch.png"
    return sketch_path if sketch_path.exists() else None


def read_prompt_file(prompt_path_or_dir: str | Path) -> Optional[str]:
    """
    Read prompt.txt from a file path or run directory.
    
    Can handle both:
    - Direct file path: /path/to/prompt.txt
    - Run directory: /path/to/run/folder (will look for run/prompt.txt)
    
    Args:
        prompt_path_or_dir: Path to prompt.txt file or run directory
        
    Returns:
        Prompt text, or None if file doesn't exist
    """
    path = Path(prompt_path_or_dir)
    
    # If it's a file and is named prompt.txt, use it directly
    if path.is_file() and path.name == "prompt.txt":
        try:
            return path.read_text()
        except IOError:
            return None
    
    # Otherwise assume it's a directory and look for prompt.txt inside
    prompt_path = path / "prompt.txt"
    
    if not prompt_path.exists():
        return None
    
    try:
        return prompt_path.read_text()
    except IOError:
        return None


def save_uploaded_sketch(uploaded_file_bytes: bytes, filename: str, sketches_dir: str | Path) -> Path:
    """
    Save uploaded sketch file safely to disk.
    
    Args:
        uploaded_file_bytes: Raw bytes from Streamlit UploadedFile.read()
        filename: Original filename from upload
        sketches_dir: Path to input/sketches directory
        
    Returns:
        Path to saved file
        
    Raises:
        IOError: If write fails
        ValueError: If directory creation fails
    """
    sketches_path = Path(sketches_dir)
    
    if not sketches_path.exists():
        sketches_path.mkdir(parents=True, exist_ok=True)
    
    safe_filename = sanitize_filename(filename)
    file_path = sketches_path / safe_filename
    
    # Write bytes to file
    file_path.write_bytes(uploaded_file_bytes)
    
    return file_path
