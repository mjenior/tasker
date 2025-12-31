"""
Tasker - Daily Task Analyzer

Analyzes daily task notes using Claude via LangChain and generates
actionable execution plans based on GTD principles.
"""

from .prompts import (
    get_daily_prompt,
    get_weekly_prompt,
    DAILY_SYSTEM_PROMPT,
    DAILY_HUMAN_PROMPT,
    WEEKLY_SYSTEM_PROMPT,
    WEEKLY_HUMAN_PROMPT,
    IMAGE_EXTRACTION_PROMPT,
)
from .tasker import (
    main,
    analyze_tasks,
    load_task_notes,
    collect_weekly_analyses,
    save_analysis,
    extract_text_from_image,
)

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
    # Prompt templates
    "get_daily_prompt",
    "get_weekly_prompt",
    "DAILY_SYSTEM_PROMPT",
    "DAILY_HUMAN_PROMPT",
    "WEEKLY_SYSTEM_PROMPT",
    "WEEKLY_HUMAN_PROMPT",
    "IMAGE_EXTRACTION_PROMPT",
]
