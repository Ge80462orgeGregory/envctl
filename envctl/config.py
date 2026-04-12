"""Configuration management for envctl.

Handles loading and saving of envctl configuration,
including supported environments and storage paths.
"""

import os
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".envctl"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_ENVS_DIR = DEFAULT_CONFIG_DIR / "envs"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1",
    "environments": ["local", "staging", "production"],
    "active_project": None,
    "envs_dir": str(DEFAULT_ENVS_DIR),
}


def ensure_config_dir() -> None:
    """Create config directories if they don't exist."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_ENVS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load configuration from disk, returning defaults if not found."""
    ensure_config_dir()
    if not DEFAULT_CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    with open(DEFAULT_CONFIG_FILE, "r") as f:
        data = json.load(f)
    # Merge with defaults to handle missing keys in older configs
    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged


def save_config(config: dict[str, Any]) -> None:
    """Persist configuration to disk."""
    ensure_config_dir()
    with open(DEFAULT_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_envs_dir(config: dict[str, Any] | None = None) -> Path:
    """Return the resolved path to the envs storage directory."""
    if config is None:
        config = load_config()
    return Path(config.get("envs_dir", str(DEFAULT_ENVS_DIR)))
