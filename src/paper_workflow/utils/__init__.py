"""
Utilities for the paper workflow framework.

- ``ConfigLoader`` — loads and caches ``default_config.yaml`` with typed accessors.
- ``reproducibility`` — environment capture, session reports, Dockerfile generation.
- ``error_tracker`` — structured error tracking replacing bare ``except: pass`` patterns.
"""

from paper_workflow.utils.config_loader import ConfigLoader
from paper_workflow.utils.error_tracker import (
    ErrorLogEntry,
    ErrorTracker,
    error_tracker_context,
)

__all__ = [
    "ConfigLoader",
    "ErrorLogEntry",
    "ErrorTracker",
    "error_tracker_context",
]
