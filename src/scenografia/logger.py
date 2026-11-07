"""Centralized logging configuration with file rotation."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "scenografia",
    log_dir: str = "logs",
    log_file: str = "scenografia_app.log"
) -> logging.Logger:
    """
    Set up and return a logger configured with rotating file and console handlers.
    
    Args:
        name: Logger name
        log_dir: Directory where logs are saved
        log_file: Log filename
        
    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (5 MB per file, max 3 backups)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
