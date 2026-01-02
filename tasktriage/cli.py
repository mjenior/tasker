#!/usr/bin/env python3
"""
Command-line interface for TaskTriage.

Provides the main entry point for analyzing daily and weekly task notes.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from .analysis import analyze_tasks
from .files import (
    load_all_unanalyzed_task_notes,
    collect_weekly_analyses,
    collect_weekly_analyses_for_week,
    save_analysis,
    get_notes_source,
)
from .image import IMAGE_EXTENSIONS


def analyze_single_file(task_notes: str, notes_path, file_date, notes_type: str) -> tuple:
    """Analyze a single task notes file.

    Args:
        task_notes: Content of the task notes
        notes_path: Path to the notes file
        file_date: Date parsed from filename
        notes_type: Type of analysis (daily/weekly)

    Returns:
        Tuple of (notes_path, output_path, success, error_message)
    """
    try:
        # Format date for the prompt
        prompt_vars = {
            "current_date": file_date.strftime("%A, %B %d, %Y"),
        }

        result = analyze_tasks(notes_type, task_notes, **prompt_vars)
        output_path = save_analysis(result, notes_path, notes_type)
        return (notes_path, output_path, True, None)
    except Exception as e:
        return (notes_path, None, False, str(e))


def main():
    """Main CLI entry point for task analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze task notes and generate execution plans"
    )
    parser.add_argument(
        "--files",
        default="png",
        choices=["png", "txt"],
        help="File type preference: png or txt (default: png)"
    )

    args = parser.parse_args()

    try:
        # Show which notes source is being used
        source = get_notes_source()
        source_label = "Google Drive" if source == "gdrive" else "USB/Local"
        print(f"Using notes source: {source_label}\n")

        # Load all unanalyzed daily files
        unanalyzed_files = load_all_unanalyzed_task_notes("daily", args.files)

        print(f"Found {len(unanalyzed_files)} unanalyzed file(s)\n")

        # Process files in parallel
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    analyze_single_file,
                    task_notes,
                    notes_path,
                    file_date,
                    "daily"
                ): notes_path
                for task_notes, notes_path, file_date in unanalyzed_files
            }

            # Process results as they complete
            for future in as_completed(future_to_file):
                notes_path, output_path, success, error_msg = future.result()

                # Indicate if text was extracted from an image
                if notes_path.suffix.lower() in IMAGE_EXTENSIONS:
                    file_type = " (image)"
                else:
                    file_type = ""

                if success:
                    print(f"✓ Analyzed: {notes_path.name}{file_type}")
                    print(f"  Saved to: {output_path}\n")
                    successful += 1
                else:
                    print(f"✗ Failed: {notes_path.name}{file_type}")
                    print(f"  Error: {error_msg}\n")
                    failed += 1

        # Print summary
        print(f"\n{'='*50}")
        print(f"Summary: {successful} successful, {failed} failed")
        print(f"{'='*50}")

        # Check for weeks needing analysis
        from .files import _find_weeks_needing_analysis
        weeks_to_analyze = _find_weeks_needing_analysis()

        if weeks_to_analyze:
            print(f"\n{'='*50}")
            print(f"Auto-triggering weekly analyses")
            print(f"{'='*50}\n")

            weekly_successful = 0
            weekly_failed = 0

            for week_start, week_end in weeks_to_analyze:
                week_label = week_start.strftime("%B %d") + " - " + week_end.strftime("%B %d, %Y")
                try:
                    print(f"Analyzing week: {week_label}")

                    # Collect and analyze
                    task_notes, notes_path, ws, we = collect_weekly_analyses_for_week(week_start, week_end)

                    prompt_vars = {
                        "week_start": ws.strftime("%A, %B %d, %Y"),
                        "week_end": we.strftime("%A, %B %d, %Y"),
                    }

                    result = analyze_tasks("weekly", task_notes, **prompt_vars)
                    output_path = save_analysis(result, notes_path, "weekly")

                    print(f"  ✓ Weekly analysis saved to: {output_path}\n")
                    weekly_successful += 1
                except Exception as e:
                    print(f"  ✗ Failed: {e}\n")
                    weekly_failed += 1

            print(f"{'='*50}")
            print(f"Weekly Summary: {weekly_successful} successful, {weekly_failed} failed")
            print(f"{'='*50}")

        if failed > 0:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
