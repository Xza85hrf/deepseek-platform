import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys


def setup_logging(logger_name="deepseek_platform"):
    """
    Set up logging configuration with both file and console handlers
    Returns a configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers = []

    # Create formatters
    verbose_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler for all logs
    main_log_file = log_dir / f"{logger_name}.log"
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(verbose_formatter)
    logger.addHandler(file_handler)

    # Error file handler
    error_log_file = log_dir / f"{logger_name}_error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(verbose_formatter)
    logger.addHandler(error_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    # Log the initialization
    logger.debug(f"Logging initialized for {logger_name}")
    logger.debug(f"Main log file: {main_log_file}")
    logger.debug(f"Error log file: {error_log_file}")

    return logger


def get_logger(name):
    """
    Get a logger instance with the specified name.
    If the logger doesn't exist, it will be created with the default configuration.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Only configure if not already configured
        return setup_logging(name)
    return logger
