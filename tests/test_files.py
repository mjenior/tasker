"""
Tests for tasker.files module.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestLoadTaskNotesUsb:
    """Tests for loading task notes from USB/local directory."""

    def test_loads_text_file(self, mock_usb_dir, sample_notes_file):
        """Should load content from a text file."""
        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            assert "Review Q4 budget proposal" in content
            assert path == sample_notes_file
            assert file_date == datetime(2025, 12, 31, 14, 30, 0)

    def test_loads_png_file_with_text_extraction(self, mock_usb_dir, sample_image_file):
        """Should extract text from PNG file using vision API."""
        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"), \
             patch("tasker.files.extract_text_from_image") as mock_extract:
            mock_extract.return_value = "Extracted task notes"

            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            assert content == "Extracted task notes"
            mock_extract.assert_called_once_with(sample_image_file)

    def test_skips_analysis_files(self, mock_usb_dir, sample_analysis_file):
        """Should skip files that are already analysis files."""
        # Create a notes file
        daily_dir = mock_usb_dir / "daily"
        notes_path = daily_dir / "20251228_100000.txt"
        notes_path.write_text("Some tasks")

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            # Should load the notes file, not the analysis file
            assert "Some tasks" in content
            assert "daily_analysis" not in path.name

    def test_skips_files_with_existing_analysis(self, mock_usb_dir):
        """Should skip notes files that already have an analysis file."""
        daily_dir = mock_usb_dir / "daily"

        # Create a notes file with existing analysis
        notes_with_analysis = daily_dir / "20251231_143000.txt"
        notes_with_analysis.write_text("Old tasks")
        analysis_file = daily_dir / "20251231_143000.daily_analysis.txt"
        analysis_file.write_text("Analysis exists")

        # Create a newer notes file without analysis
        newer_notes = daily_dir / "20251230_090000.txt"
        newer_notes.write_text("Newer tasks")

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            # Should load the file without analysis (even though it's older by name)
            assert "Newer tasks" in content

    def test_raises_when_directory_not_found(self, mock_usb_dir):
        """Should raise FileNotFoundError when directory doesn't exist."""
        with patch("tasker.files.USB_DIR", "/nonexistent/path"), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import load_task_notes

            with pytest.raises(FileNotFoundError, match="not found"):
                load_task_notes("daily")

    def test_raises_when_no_unanalyzed_files(self, mock_usb_dir):
        """Should raise FileNotFoundError when all files are analyzed."""
        daily_dir = mock_usb_dir / "daily"
        # Create only an analysis file
        analysis = daily_dir / "20251231_143000.daily_analysis.txt"
        analysis.write_text("Analysis content")

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import load_task_notes

            with pytest.raises(FileNotFoundError, match="No unanalyzed"):
                load_task_notes("daily")


class TestLoadTaskNotesGdrive:
    """Tests for loading task notes from Google Drive."""

    def test_loads_text_file_from_gdrive(self):
        """Should load text file content from Google Drive."""
        mock_client = MagicMock()
        mock_client.list_notes_files.return_value = [
            {"id": "file1", "name": "20251231_143000.txt", "mimeType": "text/plain"}
        ]
        mock_client.file_exists.return_value = False
        mock_client.download_file_text.return_value = "GDrive task content"

        with patch("tasker.files.get_active_source", return_value="gdrive"), \
             patch("tasker.gdrive.GoogleDriveClient", return_value=mock_client):
            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            assert content == "GDrive task content"
            assert "gdrive:" in str(path)  # Path normalizes gdrive:// to gdrive:/
            assert file_date == datetime(2025, 12, 31, 14, 30, 0)

    def test_extracts_text_from_png_in_gdrive(self, temp_dir):
        """Should extract text from PNG files in Google Drive."""
        mock_client = MagicMock()
        mock_client.list_notes_files.return_value = [
            {"id": "file1", "name": "20251230_090000.png", "mimeType": "image/png"}
        ]
        mock_client.file_exists.return_value = False
        # Return minimal PNG bytes
        mock_client.download_file.return_value = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])

        with patch("tasker.files.get_active_source", return_value="gdrive"), \
             patch("tasker.gdrive.GoogleDriveClient", return_value=mock_client), \
             patch("tasker.files.extract_text_from_image") as mock_extract:
            mock_extract.return_value = "Extracted from GDrive image"

            from tasker.files import load_task_notes

            content, path, file_date = load_task_notes("daily")

            assert content == "Extracted from GDrive image"


class TestCollectWeeklyAnalysesUsb:
    """Tests for collecting weekly analyses from USB."""

    def test_collects_analyses_from_previous_week(self, mock_usb_dir):
        """Should collect all daily analyses from the previous week."""
        daily_dir = mock_usb_dir / "daily"

        # Calculate dates for last week
        today = datetime.now()
        days_since_sunday = (today.weekday() + 1) % 7
        last_sunday = today - timedelta(days=days_since_sunday)
        last_monday = last_sunday - timedelta(days=6)

        # Create analysis files for last week
        for i, day in enumerate([last_monday, last_monday + timedelta(days=2)]):
            timestamp = day.strftime("%Y%m%d_080000")
            analysis_path = daily_dir / f"{timestamp}.daily_analysis.txt"
            analysis_path.write_text(f"Analysis for day {i + 1}")

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import collect_weekly_analyses

            combined, output_path, week_start, week_end = collect_weekly_analyses()

            assert "Analysis for day 1" in combined
            assert "Analysis for day 2" in combined
            assert "weekly" in str(output_path)

    def test_creates_weekly_directory_if_missing(self, mock_usb_dir):
        """Should create weekly directory if it doesn't exist."""
        # Remove weekly directory
        weekly_dir = mock_usb_dir / "weekly"
        weekly_dir.rmdir()

        daily_dir = mock_usb_dir / "daily"

        # Create at least one analysis file
        today = datetime.now()
        days_since_sunday = (today.weekday() + 1) % 7
        last_sunday = today - timedelta(days=days_since_sunday)
        last_monday = last_sunday - timedelta(days=6)
        timestamp = last_monday.strftime("%Y%m%d_080000")
        (daily_dir / f"{timestamp}.daily_analysis.txt").write_text("Analysis")

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import collect_weekly_analyses

            collect_weekly_analyses()

            assert weekly_dir.exists()

    def test_raises_when_no_analyses_found(self, mock_usb_dir):
        """Should raise FileNotFoundError when no analyses found for the week."""
        with patch("tasker.files.USB_DIR", str(mock_usb_dir)), \
             patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import collect_weekly_analyses

            with pytest.raises(FileNotFoundError, match="No daily analysis files"):
                collect_weekly_analyses()


class TestSaveAnalysis:
    """Tests for saving analysis files."""

    def test_saves_analysis_to_usb(self, mock_usb_dir, sample_notes_file):
        """Should save analysis file next to the input file."""
        from tasker.files import save_analysis

        analysis_content = "# Daily Execution Order\n\n1. Task one"

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)):
            output_path = save_analysis(analysis_content, sample_notes_file, "daily")

            assert output_path.exists()
            assert "daily_analysis" in output_path.name
            content = output_path.read_text()
            assert "Daily Task Analysis" in content
            assert "Task one" in content

    def test_saves_analysis_to_gdrive(self, mock_usb_dir):
        """Should upload analysis to Google Drive for gdrive:// paths."""
        mock_client = MagicMock()

        with patch("tasker.gdrive.GoogleDriveClient", return_value=mock_client):
            from tasker.files import _save_analysis_gdrive

            # Test the gdrive function directly since Path normalizes gdrive://
            virtual_path = Path("gdrive://daily/20251231_143000.txt")
            analysis_content = "Analysis content"

            output_path = _save_analysis_gdrive(analysis_content, virtual_path, "daily")

            mock_client.upload_file.assert_called_once()
            assert "gdrive:" in str(output_path)

    def test_formats_output_with_header(self, mock_usb_dir, sample_notes_file):
        """Should format output with proper header."""
        from tasker.files import save_analysis

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)):
            output_path = save_analysis("Content", sample_notes_file, "daily")

            content = output_path.read_text()
            assert "Daily Task Analysis" in content
            assert "=" * 40 in content

    def test_always_saves_as_txt(self, mock_usb_dir):
        """Should always save as .txt regardless of input format."""
        daily_dir = mock_usb_dir / "daily"
        png_input = daily_dir / "20251230_090000.png"
        png_input.write_bytes(b"fake png data")

        from tasker.files import save_analysis

        with patch("tasker.files.USB_DIR", str(mock_usb_dir)):
            output_path = save_analysis("Analysis", png_input, "daily")

            assert output_path.suffix == ".txt"


class TestGetNotesSource:
    """Tests for get_notes_source function."""

    def test_returns_usb_when_usb_active(self):
        """Should return 'usb' when USB source is active."""
        with patch("tasker.files.get_active_source", return_value="usb"):
            from tasker.files import get_notes_source

            result = get_notes_source()
            assert result == "usb"

    def test_returns_gdrive_when_gdrive_active(self):
        """Should return 'gdrive' when Google Drive source is active."""
        with patch("tasker.files.get_active_source", return_value="gdrive"):
            from tasker.files import get_notes_source

            result = get_notes_source()
            assert result == "gdrive"


class TestFileExtensionConstants:
    """Tests for file extension constants."""

    def test_text_extensions_contains_txt(self):
        """TEXT_EXTENSIONS should include .txt."""
        from tasker.files import TEXT_EXTENSIONS

        assert ".txt" in TEXT_EXTENSIONS

    def test_all_extensions_includes_both(self):
        """ALL_EXTENSIONS should include both text and image extensions."""
        from tasker.files import ALL_EXTENSIONS, TEXT_EXTENSIONS
        from tasker.image import IMAGE_EXTENSIONS

        assert TEXT_EXTENSIONS.issubset(ALL_EXTENSIONS)
        assert IMAGE_EXTENSIONS.issubset(ALL_EXTENSIONS)
