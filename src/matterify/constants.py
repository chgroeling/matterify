"""Constants used across the project."""

import os

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    "**/.git",
    "**/.obsidian",
    "**/__pycache__",
    "**/.venv",
    "**/venv",
    "**/node_modules",
    "**/.mypy_cache",
    "**/.pytest_cache",
    "**/.ruff_cache",
)

DEFAULT_N_PROCS = os.cpu_count() or 1
