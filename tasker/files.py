"""
File I/O operations for Tasker.

Handles loading task notes, collecting analyses, and saving output files.
"""

from datetime import datetime, timedelta
from pathlib import Path

from .config import USB_DIR
from .image import extract_text_from_image, IMAGE_EXTENSIONS

# Supported text file extensions
TEXT_EXTENSIONS = {".txt"}

# All supported input file extensions
ALL_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS


def load_task_notes(notes_type: str = "daily") -> tuple[str, Path, datetime]:
    """Load the most recent task notes file that hasn't been analyzed yet.

    Supports both .txt files (read directly) and image files (.png, .jpg, .jpeg,
    .gif, .webp) which are processed through Claude's vision API to extract text.

    Args:
        notes_type: Type of notes to load (e.g., "daily", "weekly")

    Returns:
        Tuple of (file contents, path to the notes file, parsed datetime from filename)

    Raises:
        FileNotFoundError: If the notes directory doesn't exist or no unanalyzed files found
    """
    base_dir = Path(USB_DIR)

    # Check if flash drive is mounted
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Flash drive not mounted. Expected notes directory at: {USB_DIR}"
        )

    notes_dir = base_dir / notes_type

    if not notes_dir.exists():
        raise FileNotFoundError(f"Notes directory not found: {notes_dir}")

    # Find all supported files and sort by modification time (newest first)
    all_files = []
    for ext in ALL_EXTENSIONS:
        all_files.extend(notes_dir.glob(f"*{ext}"))
    all_files = sorted(all_files, reverse=True)

    for notes_path in all_files:
        # Skip files that are already analysis files
        if "_analysis" in notes_path.name:
            continue

        # Check if this file already has an associated analysis file
        # Analysis files are always .txt regardless of input format
        analysis_filename = f"{notes_path.stem}.{notes_type}_analysis.txt"
        analysis_path = notes_dir / analysis_filename

        if not analysis_path.exists():
            # Parse datetime from filename (format: YYYYMMDD_HHMMSS.ext)
            date_str = notes_path.stem
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")

            # Extract text based on file type
            if notes_path.suffix.lower() in IMAGE_EXTENSIONS:
                # Use vision API to extract text from image
                file_contents = extract_text_from_image(notes_path)
            else:
                # Read text file directly
                file_contents = notes_path.read_text()

            return file_contents, notes_path, file_date

    raise FileNotFoundError(
        f"No unanalyzed notes files found in: {notes_dir}"
    )


def collect_weekly_analyses() -> tuple[str, Path, datetime, datetime]:
    """Collect all daily analysis files from the previous week.

    Returns:
        Tuple of (combined analysis text, output path for weekly analysis,
                  week start datetime, week end datetime)

    Raises:
        FileNotFoundError: If directories don't exist or no analyses found for the week
    """
    base_dir = Path(USB_DIR)

    # Check if flash drive is mounted
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Flash drive not mounted. Expected notes directory at: {USB_DIR}"
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
            f"No daily analysis files found for the week of "
            f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        )

    # Combine all analyses with labels
    combined_text = "\n\n---\n\n".join(collected_analyses)

    # Create output path for weekly analysis
    week_label = week_start.strftime("%Y%m%d")
    output_path = weekly_dir / f"{week_label}.week.txt"

    return combined_text, output_path, week_start, week_end


def save_analysis(analysis: str, input_path: Path, notes_type: str = "daily") -> Path:
    """Save the analysis output to a file.

    Args:
        analysis: The analysis content from analyze_tasks
        input_path: Path to the original notes file
        notes_type: Type of analysis (e.g., "daily", "weekly")

    Returns:
        Path to the saved analysis file
    """
    # Create output filename: {stem}.{type}_analysis.txt
    # Always use .txt extension regardless of input format
    output_filename = f"{input_path.stem}.{notes_type}_analysis.txt"
    output_path = input_path.parent / output_filename

    # Format the output
    header = f"{notes_type.capitalize()} Task Analysis"
    formatted_output = f"{header}\n{'=' * 40}\n\n{analysis}\n"

    output_path.write_text(formatted_output)
    return output_path
