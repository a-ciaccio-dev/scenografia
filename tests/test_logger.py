"""Unit tests for centralized rotating logger."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tempfile
from scenografia.logger import setup_logger


def test_setup_logger_creates_directory_and_handlers():
    """Verify logger creates log directory and configures RotatingFileHandler."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_logger_name = "test_scenografia_logger_unique"
        logger = setup_logger(name=test_logger_name, log_dir=tmp_dir, log_file="test.log")
        
        try:
            assert logger.name == test_logger_name
            assert logger.level == logging.INFO
            
            # Verify RotatingFileHandler exists and has rotation limits
            file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
            assert len(file_handlers) >= 1
            rfh = file_handlers[0]
            assert rfh.maxBytes == 5 * 1024 * 1024
            assert rfh.backupCount == 3
            
            # Verify file is written
            logger.info("Test message for rotating log")
            log_file = Path(tmp_dir) / "test.log"
            assert log_file.exists()
            assert "Test message for rotating log" in log_file.read_text(encoding="utf-8")
        finally:
            # Release file handles on Windows before TemporaryDirectory cleanup
            for h in list(logger.handlers):
                h.close()
                logger.removeHandler(h)
