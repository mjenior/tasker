"""
Tests for tasktriage.config module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml


class TestFetchApiKey:
    """Tests for fetch_api_key function."""

    def test_returns_provided_api_key(self):
        """Should return the API key when provided directly."""
        from tasktriage.config import fetch_api_key

        result = fetch_api_key("my-direct-api-key")
        assert result == "my-direct-api-key"

    def test_returns_env_var_when_no_key_provided(self, monkeypatch):
        """Should return ANTHROPIC_API_KEY from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-api-key-12345")
        from tasktriage.config import fetch_api_key

        result = fetch_api_key(None)
        assert result == "env-api-key-12345"

    def test_raises_when_no_key_available(self, monkeypatch):
        """Should raise ValueError when no API key is available."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from tasktriage.config import fetch_api_key

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            fetch_api_key(None)


class TestLoadModelConfig:
    """Tests for load_model_config function."""

    def test_returns_empty_dict_when_no_config_file(self, temp_dir):
        """Should return empty dict when config.yaml doesn't exist."""
        import tasktriage.config

        # Save original and patch
        original_path = tasktriage.config.CONFIG_PATH
        tasktriage.config.CONFIG_PATH = temp_dir / "nonexistent.yaml"

        try:
            result = tasktriage.config.load_model_config()
            assert result == {}
        finally:
            tasktriage.config.CONFIG_PATH = original_path

    def test_loads_config_from_yaml(self, temp_dir):
        """Should load and return configuration from YAML file."""
        import tasktriage.config

        config_path = temp_dir / "config.yaml"
        config_data = {
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.5,
            "max_tokens": 2048,
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Save original and patch
        original_path = tasktriage.config.CONFIG_PATH
        tasktriage.config.CONFIG_PATH = config_path

        try:
            result = tasktriage.config.load_model_config()
            assert result["model"] == "claude-sonnet-4-20250514"
            assert result["temperature"] == 0.5
            assert result["max_tokens"] == 2048
        finally:
            tasktriage.config.CONFIG_PATH = original_path

    def test_returns_empty_dict_for_empty_yaml(self, temp_dir):
        """Should return empty dict for empty YAML file."""
        import tasktriage.config

        config_path = temp_dir / "config.yaml"
        config_path.write_text("")

        # Save original and patch
        original_path = tasktriage.config.CONFIG_PATH
        tasktriage.config.CONFIG_PATH = config_path

        try:
            result = tasktriage.config.load_model_config()
            assert result == {}
        finally:
            tasktriage.config.CONFIG_PATH = original_path


class TestIsUsbAvailable:
    """Tests for is_usb_available function."""

    def test_returns_true_when_usb_dir_exists(self, temp_dir):
        """Should return True when EXTERNAL_INPUT_DIR exists."""
        import tasktriage.config

        original = tasktriage.config.EXTERNAL_INPUT_DIR
        try:
            tasktriage.config.EXTERNAL_INPUT_DIR = str(temp_dir)
            result = tasktriage.config.is_usb_available()
            assert result is True
        finally:
            tasktriage.config.EXTERNAL_INPUT_DIR = original

    def test_returns_false_when_usb_dir_not_set(self):
        """Should return False when EXTERNAL_INPUT_DIR is not set."""
        import tasktriage.config

        original = tasktriage.config.EXTERNAL_INPUT_DIR
        try:
            tasktriage.config.EXTERNAL_INPUT_DIR = None
            result = tasktriage.config.is_usb_available()
            assert result is False
        finally:
            tasktriage.config.EXTERNAL_INPUT_DIR = original

    def test_returns_false_when_usb_dir_doesnt_exist(self):
        """Should return False when EXTERNAL_INPUT_DIR path doesn't exist."""
        import tasktriage.config

        original = tasktriage.config.EXTERNAL_INPUT_DIR
        try:
            tasktriage.config.EXTERNAL_INPUT_DIR = "/nonexistent/path"
            result = tasktriage.config.is_usb_available()
            assert result is False
        finally:
            tasktriage.config.EXTERNAL_INPUT_DIR = original


class TestIsGdriveAvailable:
    """Tests for is_gdrive_available function (OAuth-based)."""

    def test_returns_true_when_credentials_exist(self):
        """Should return True when Google Drive OAuth is properly configured."""
        import tasktriage.config

        orig_id = tasktriage.config.GOOGLE_OAUTH_CLIENT_ID
        orig_secret = tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET
        orig_folder = tasktriage.config.GOOGLE_DRIVE_FOLDER_ID
        try:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = "test-folder-id"
            result = tasktriage.config.is_gdrive_available()
            assert result is True
        finally:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = orig_id
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = orig_secret
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = orig_folder

    def test_returns_false_when_client_id_not_set(self):
        """Should return False when GOOGLE_OAUTH_CLIENT_ID is not set."""
        import tasktriage.config

        orig_id = tasktriage.config.GOOGLE_OAUTH_CLIENT_ID
        orig_secret = tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET
        orig_folder = tasktriage.config.GOOGLE_DRIVE_FOLDER_ID
        try:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = None
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = "test-folder-id"
            result = tasktriage.config.is_gdrive_available()
            assert result is False
        finally:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = orig_id
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = orig_secret
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = orig_folder

    def test_returns_false_when_folder_id_not_set(self):
        """Should return False when GOOGLE_DRIVE_FOLDER_ID is not set."""
        import tasktriage.config

        orig_id = tasktriage.config.GOOGLE_OAUTH_CLIENT_ID
        orig_secret = tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET
        orig_folder = tasktriage.config.GOOGLE_DRIVE_FOLDER_ID
        try:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = "test-client-secret"
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = None
            result = tasktriage.config.is_gdrive_available()
            assert result is False
        finally:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = orig_id
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = orig_secret
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = orig_folder

    def test_returns_false_when_client_secret_not_set(self):
        """Should return False when GOOGLE_OAUTH_CLIENT_SECRET is not set."""
        import tasktriage.config

        orig_id = tasktriage.config.GOOGLE_OAUTH_CLIENT_ID
        orig_secret = tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET
        orig_folder = tasktriage.config.GOOGLE_DRIVE_FOLDER_ID
        try:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = "test-client-id"
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = None
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = "test-folder-id"
            result = tasktriage.config.is_gdrive_available()
            assert result is False
        finally:
            tasktriage.config.GOOGLE_OAUTH_CLIENT_ID = orig_id
            tasktriage.config.GOOGLE_OAUTH_CLIENT_SECRET = orig_secret
            tasktriage.config.GOOGLE_DRIVE_FOLDER_ID = orig_folder


class TestGetActiveSource:
    """Tests for get_active_source function."""

    def test_returns_usb_when_notes_source_is_usb(self, temp_dir):
        """Should return 'usb' when NOTES_SOURCE is 'usb' and USB is available."""
        with patch("tasktriage.config.NOTES_SOURCE", "usb"), \
             patch("tasktriage.config.is_usb_available", return_value=True):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "usb"

            result = tasktriage.config.get_active_source()
            assert result == "usb"

    def test_returns_gdrive_when_notes_source_is_gdrive(self, temp_dir):
        """Should return 'gdrive' when NOTES_SOURCE is 'gdrive' and GDrive is available."""
        credentials_path = temp_dir / "credentials.json"
        credentials_path.write_text('{"type": "service_account"}')

        with patch("tasktriage.config.NOTES_SOURCE", "gdrive"), \
             patch("tasktriage.config.is_gdrive_available", return_value=True):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "gdrive"

            result = tasktriage.config.get_active_source()
            assert result == "gdrive"

    def test_raises_when_usb_requested_but_unavailable(self):
        """Should raise ValueError when USB is requested but not available."""
        with patch("tasktriage.config.NOTES_SOURCE", "usb"), \
             patch("tasktriage.config.is_usb_available", return_value=False):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "usb"

            with pytest.raises(ValueError, match="USB source requested"):
                tasktriage.config.get_active_source()

    def test_raises_when_gdrive_requested_but_unavailable(self):
        """Should raise ValueError when GDrive is requested but not available."""
        with patch("tasktriage.config.NOTES_SOURCE", "gdrive"), \
             patch("tasktriage.config.is_gdrive_available", return_value=False):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "gdrive"

            with pytest.raises(ValueError, match="Google Drive source requested"):
                tasktriage.config.get_active_source()

    def test_auto_prefers_usb_when_both_available(self, temp_dir):
        """Should prefer USB over GDrive in auto mode when both are available."""
        with patch("tasktriage.config.NOTES_SOURCE", "auto"), \
             patch("tasktriage.config.is_usb_available", return_value=True), \
             patch("tasktriage.config.is_gdrive_available", return_value=True):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "auto"

            result = tasktriage.config.get_active_source()
            assert result == "usb"

    def test_auto_falls_back_to_gdrive(self, temp_dir):
        """Should fall back to GDrive in auto mode when USB is unavailable."""
        with patch("tasktriage.config.NOTES_SOURCE", "auto"), \
             patch("tasktriage.config.is_usb_available", return_value=False), \
             patch("tasktriage.config.is_gdrive_available", return_value=True):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "auto"

            result = tasktriage.config.get_active_source()
            assert result == "gdrive"

    def test_auto_raises_when_no_source_available(self):
        """Should raise ValueError when no source is available in auto mode."""
        with patch("tasktriage.config.NOTES_SOURCE", "auto"), \
             patch("tasktriage.config.is_usb_available", return_value=False), \
             patch("tasktriage.config.is_gdrive_available", return_value=False):
            import tasktriage.config
            tasktriage.config.NOTES_SOURCE = "auto"

            with pytest.raises(ValueError, match="No notes source available"):
                tasktriage.config.get_active_source()
