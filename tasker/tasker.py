#!/usr/bin/env python3
"""
Daily + Weekly Task Analyzer

Analyzes daily task notes using Claude via LangChain and generates
an actionable execution plan based on GTD principles.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from .prompts import get_daily_prompt, get_weekly_prompt

# Load environment variables from .env file (looks in repo root)
load_dotenv(Path(__file__).parent.parent / ".env")

# Notes directory from environment variable
NOTES_DIR = os.getenv("NOTES_DIR")
if not NOTES_DIR:
    raise ValueError(
        "NOTES_DIR environment variable is not set. "
        "Please create a .env file from .env.template and set NOTES_DIR."
    )

# Path to model configuration file (at repository root, parent of package)
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def fetch_api_key(api_key: str | None = None) -> str:
    """Get Anthropic API key"""
    if api_key:
        return api_key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return api_key


def load_model_config() -> dict:
    """Load model configuration from YAML file.

    Returns:
        Dictionary of configuration parameters
    """
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    return config or {}


def load_task_notes(notes_type: str = "daily") -> tuple[str, Path, datetime]:
    """Load the most recent task notes file that hasn't been analyzed yet.

    Args:
        notes_type: Type of notes to load (e.g., "daily", "weekly")

    Returns:
        Tuple of (file contents, path to the notes file, parsed datetime from filename)
    """
    base_dir = Path(NOTES_DIR)

    # Check if flash drive is mounted
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Flash drive not mounted. Expected notes directory at: {NOTES_DIR}"
        )

    notes_dir = base_dir / notes_type

    if not notes_dir.exists():
        raise FileNotFoundError(f"Notes directory not found: {notes_dir}")

    # Find most recent file without an associated analysis file
    # Files are named with timestamp prefix: YYYYMMDD_HHMMSS.txt
    txt_files = sorted(notes_dir.glob("*.txt"), reverse=True)

    for notes_path in txt_files:
        # Skip files that are already analysis files
        if "_analysis" in notes_path.name:
            continue

        # Check if this file already has an associated analysis file
        analysis_filename = f"{notes_path.stem}.{notes_type}_analysis{notes_path.suffix}"
        analysis_path = notes_dir / analysis_filename

        if not analysis_path.exists():
            # Parse datetime from filename (format: YYYYMMDD_HHMMSS.txt)
            date_str = notes_path.stem
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            return notes_path.read_text(), notes_path, file_date

    raise FileNotFoundError(
        f"No unanalyzed notes files found in: {notes_dir}"
    )


def collect_weekly_analyses() -> tuple[str, Path, datetime, datetime]:
    """Collect all daily analysis files from the previous week.

    Returns:
        Tuple of (combined analysis text, output path for weekly analysis,
                  week start datetime, week end datetime)
    """
    base_dir = Path(NOTES_DIR)

    # Check if flash drive is mounted
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Flash drive not mounted. Expected notes directory at: {NOTES_DIR}"
        )

    daily_dir = base_dir / "daily"
    weekly_dir = base_dir / "weekly"

    if not daily_dir.exists():
        raise FileNotFoundError(f"Daily notes directory not found: {daily_dir}")

    # Create weekly directory if it doesn't exist
    weekly_dir.mkdir(exist_ok=True)

    # Calculate previous week's date range (Monday to Sunday)
    today = datetime.now()
    # Find last Sunday (end of previous week)
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    # Find the Monday of that week
    last_monday = last_sunday - timedelta(days=6)

    # Set to start/end of day for comparison
    week_start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = last_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Find all daily_analysis files from the previous week
    analysis_files = sorted(daily_dir.glob("*.daily_analysis.txt"))

    collected_analyses = []
    for analysis_path in analysis_files:
        # Parse date from filename (format: YYYYMMDD_HHMMSS.daily_analysis.txt)
        try:
            date_str = analysis_path.stem.split(".")[0]  # Get YYYYMMDD_HHMMSS part
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        except ValueError:
            continue

        # Check if file is within the previous week
        if week_start <= file_date <= week_end:
            content = analysis_path.read_text()
            date_label = file_date.strftime("%A, %B %d, %Y")
            collected_analyses.append(f"## {date_label}\n\n{content}")

    if not collected_analyses:
        raise FileNotFoundError(
            f"No daily analysis files found for the week of {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        )

    # Combine all analyses with labels
    combined_text = "\n\n---\n\n".join(collected_analyses)

    # Create output path for weekly analysis
    week_label = week_start.strftime("%Y%m%d")
    output_path = weekly_dir / f"{week_label}.week.txt"

    return combined_text, output_path, week_start, week_end


def analyze_tasks(
    analysis_type: str,
    task_notes: str,
    api_key: str | None = None,
    **prompt_vars
) -> str:
    """
    Analyze task notes using Claude via LangChain.

    Args:
        analysis_type: Type of analysis ("daily" or "weekly")
        task_notes: The task notes to analyze
        api_key: Optional Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        **prompt_vars: Variables to inject into the prompt template
            - For daily: current_date (str)
            - For weekly: week_start (str), week_end (str)

    Returns:
        The analysis and execution plan
    """
    config = load_model_config()

    # Extract model from config or use default
    model = config.pop("model", "claude-haiku-4-5-20241022")

    # Build ChatAnthropic with config parameters
    llm = ChatAnthropic(
        model=model,
        api_key=fetch_api_key(api_key),
        **config
    )

    # Get the appropriate prompt template
    if analysis_type == "weekly":
        prompt = get_weekly_prompt()
    else:
        prompt = get_daily_prompt()

    # Create the chain: prompt | llm
    chain = prompt | llm

    # Invoke with task_notes and any additional prompt variables
    response = chain.invoke({"task_notes": task_notes, **prompt_vars})
    return response.content


def save_analysis(analysis: str, input_path: Path, notes_type: str = "daily") -> Path:
    """Save the analysis output to a file.

    Args:
        analysis: The analysis content from analyze_tasks
        input_path: Path to the original notes file
        notes_type: Type of analysis (e.g., "daily", "weekly")

    Returns:
        Path to the saved analysis file
    """
    # Create output filename: {stem}.{type}_analysis{suffix}
    output_filename = f"{input_path.stem}.{notes_type}_analysis{input_path.suffix}"
    output_path = input_path.parent / output_filename

    # Format the output
    header = f"{notes_type.capitalize()} Task Analysis"
    formatted_output = f"{header}\n{'=' * 40}\n\n{analysis}\n"

    output_path.write_text(formatted_output)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Analyze daily task notes and generate an execution plan"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="daily",
        help="Analysis type: daily or weekly (default: daily)"
    )

    args = parser.parse_args()

    try:
        if args.type == "weekly":
            # Collect previous week's daily analyses
            task_notes, notes_path, week_start, week_end = collect_weekly_analyses()
            print(f"Collecting daily analyses for weekly review...\n")

            # Format dates for the prompt
            prompt_vars = {
                "week_start": week_start.strftime("%A, %B %d, %Y"),
                "week_end": week_end.strftime("%A, %B %d, %Y"),
            }
        else:
            task_notes, notes_path, file_date = load_task_notes(args.type)
            print(f"Analyzing daily tasks: {notes_path.name}\n")

            # Format date for the prompt
            prompt_vars = {
                "current_date": file_date.strftime("%A, %B %d, %Y"),
            }

        result = analyze_tasks(args.type, task_notes, **prompt_vars)

        output_path = save_analysis(result, notes_path, args.type)
        print(f"\nAnalysis saved to: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
