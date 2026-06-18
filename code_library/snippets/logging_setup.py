"""
Logging Setup Snippet - Structured logging configuration.

Usage:
    from snippets.logging_setup import setup_logging

    logger = setup_logging("my_module")
    logger.info("Processing", extra={"sample_id": "sample1"})
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    structured: bool = True,
) -> logging.Logger:
    """
    Setup structured logging with colored console output.

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for JSON logs
        structured: If True, output JSON to file

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # Color codes
    RESET = "\033[0m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"

    class ColoredFormatter(logging.Formatter):
        """Human-readable formatter with colors."""

        def format(self, record):
            level = record.levelname
            if level == "ERROR":
                color = RED
            elif level == "WARNING":
                color = YELLOW
            elif level == "INFO":
                color = GREEN
            elif level == "DEBUG":
                color = BLUE
            else:
                color = RESET

            time_str = datetime.now().strftime("%H:%M:%S")
            msg = f"{color}[{time_str}] {level:8s} | {record.getMessage()}{RESET}"

            if hasattr(record, "extra") and record.extra:
                extra_str = " ".join(f"{k}={v}" for k, v in record.extra.items())
                msg += f" | {extra_str}"

            return msg

    class JSONFormatter(logging.Formatter):
        """JSON formatter for file output."""

        def format(self, record):
            return json.dumps({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            })

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(ColoredFormatter())
    logger.addHandler(console)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        if structured:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            ))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logging(name)
