"""
Configuration loader for the RAG evaluation framework.

Loads ``config/settings.yaml`` and provides convenient access to
settings with dot-notation-style nested dictionaries.

Usage:
    >>> from approaches.common.config_loader import load_config
    >>> cfg = load_config()
    >>> print(cfg["models"]["generation_model"])
    gpt-4o-mini
"""

from __future__ import annotations

import os

import yaml


def load_config(config_path: str | None = None) -> dict:
    """Load the global settings YAML configuration.

    Resolves the config path relative to the project root (two levels
    up from this file's location in ``approaches/common/``).

    Args:
        config_path: Explicit path to ``settings.yaml``. If ``None``,
            defaults to ``<project_root>/config/settings.yaml``.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if config_path is None:
        # Resolve project root: this file is at approaches/common/config_loader.py
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        config_path = os.path.join(project_root, "config", "settings.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_project_root() -> str:
    """Return the absolute path to the project root directory.

    Returns:
        Absolute path string.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
