# config/logging_config.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import config.settings as settings


def setup_logging():
    """Configure structured logging for the entire application."""

    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "system.log")
    
    # Get log level from settings or default to INFO
    log_level_str = getattr(settings, 'LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Define Format
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(log_level)

    # File handler with rotation (10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(log_level)

    # Root logger configuration
    root = logging.getLogger()
    root.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicate logs
    if root.hasHandlers():
        root.handlers.clear()
        
    root.addHandler(console)
    root.addHandler(file_handler)

    # Reduce noise from chatty libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pycelonis").setLevel(logging.ERROR)

    logging.info("Logging initialized | level=%s | file=%s", log_level_str, log_file)