"""Directory traversal with blacklist filtering."""

from collections.abc import Iterable
from pathlib import Path

BLACKLIST: tuple[str, ...] = (
    ".git",
    ".obsidian",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
)

_MARKDOWN_SUFFIXES = {".md", ".markdown"}


def iter_markdown_files(
    root: Path,
    blacklist: tuple[str, ...] = BLACKLIST,
) -> Iterable[Path]:
    """Yield absolute paths to Markdown files under root.

    Recursively walks the directory tree, pruning blacklisted directories
    in-place to avoid unnecessary I/O.

    Args:
        root: Root directory to scan.
        blacklist: Directory names to exclude from traversal.

    Yields:
        Absolute paths to discovered Markdown files.
    """
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in blacklist]
        for filename in filenames:
            suffix = Path(filename).suffix.lower()
            if suffix in _MARKDOWN_SUFFIXES:
                yield dirpath / filename
