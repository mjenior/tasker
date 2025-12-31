"""
Tasker - Daily Task Analyzer

Analyzes daily task notes using Claude via LangChain and generates
actionable execution plans based on GTD principles.
"""

# Configuration
from .config import (
    fetch_api_key,
    load_model_config,
    USB_DIR,
    CONFIG_PATH,
    DEFAULT_MODEL,
)

# Prompt templates
from .prompts import (
    get_daily_prompt,
    get_weekly_prompt,
    DAILY_SYSTEM_PROMPT,
    DAILY_HUMAN_PROMPT,
    WEEKLY_SYSTEM_PROMPT,
    WEEKLY_HUMAN_PROMPT,
    IMAGE_EXTRACTION_PROMPT,
)

# Image processing
from .image import (
    extract_text_from_image,
    IMAGE_EXTENSIONS,
    MEDIA_TYPE_MAP,
)

# File operations
from .files import (
    load_task_notes,
    collect_weekly_analyses,
    save_analysis,
    TEXT_EXTENSIONS,
    ALL_EXTENSIONS,
)

# Core analysis
from .analysis import analyze_tasks

# CLI entry point
from .cli import main

__version__ = "0.1.0"

__all__ = [
    # Main entry point
    "main",
    # Core functions
    "analyze_tasks",
    "load_task_notes",
    "collect_weekly_analyses",
    "save_analysis",
    "extract_text_from_image",
    # Configuration
    "fetch_api_key",
    "load_model_config",
    "USB_DIR",
    "CONFIG_PATH",
    "DEFAULT_MODEL",
    # Prompt templates
    "get_daily_prompt",
    "get_weekly_prompt",
    "DAILY_SYSTEM_PROMPT",
    "DAILY_HUMAN_PROMPT",
    "WEEKLY_SYSTEM_PROMPT",
    "WEEKLY_HUMAN_PROMPT",
    "IMAGE_EXTRACTION_PROMPT",
    # Constants
    "IMAGE_EXTENSIONS",
    "MEDIA_TYPE_MAP",
    "TEXT_EXTENSIONS",
    "ALL_EXTENSIONS",
]
