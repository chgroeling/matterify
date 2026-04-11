"""Directory traversal with glob-based exclusion filtering."""

from collections.abc import Iterable
from pathlib import Path

from structlog import get_logger

from matterify.constants import DEFAULT_EXCLUDE_PATTERNS

logger = get_logger(__name__)

_MARKDOWN_SUFFIXES = {".md", ".markdown"}


def _matches_any_pattern(path: Path, patterns: tuple[str, ...]) -> bool:
    """Check if path matches any of the glob patterns."""
    return any(path.match(pat) for pat in patterns)


def iter_markdown_files(
    root: Path,
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS,
) -> Iterable[Path]:
    """Yield relative paths to Markdown files under root.

    Recursively walks the directory tree, pruning excluded directories
    in-place to avoid unnecessary I/O.

    Args:
        root: Root directory to scan.
        exclude: Glob patterns to exclude from traversal (e.g., "**/.git").

    Yields:
        Relative paths to discovered Markdown files.
    """
    logger.debug("starting_directory_traversal", root=str(root), exclude=exclude)

    discovered_count = 0

    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if not _matches_any_pattern(dirpath / d, exclude)]
        for filename in filenames:
            filepath = dirpath / filename
            if _matches_any_pattern(filepath, exclude):
                continue
            suffix = Path(filename).suffix.lower()
            if suffix in _MARKDOWN_SUFFIXES:
                discovered_count += 1
                yield filepath.relative_to(root)

    logger.debug("files_discovered", count=discovered_count, root=str(root))
