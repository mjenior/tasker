"""
Configuration management for Tasker.

Handles environment variables, API keys, and model configuration.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file (looks in repo root)
load_dotenv(Path(__file__).parent.parent / ".env")

# Notes directory from environment variable
USB_DIR = os.getenv("USB_DIR")
if not USB_DIR:
    raise ValueError(
        "USB_DIR environment variable is not set. "
        "Please create a .env file from .env.template and set USB_DIR."
    )

# Path to model configuration file (at repository root, parent of package)
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

# Default model to use if not specified in config
DEFAULT_MODEL = "claude-haiku-4-5-20241022"


def fetch_api_key(api_key: str | None = None) -> str:
    """Get Anthropic API key.

    Args:
        api_key: Optional API key to use directly

    Returns:
        The API key string

    Raises:
        ValueError: If no API key is available
    """
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
