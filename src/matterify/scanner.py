"""Directory traversal with blacklist filtering."""

from collections.abc import Iterable
from pathlib import Path

from structlog import get_logger

from matterify.constants import BLACKLIST

logger = get_logger(__name__)

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
    logger.debug("starting_directory_traversal", root=str(root), blacklist=blacklist)

    file_paths: list[Path] = []
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in blacklist]
        for filename in filenames:
            suffix = Path(filename).suffix.lower()
            if suffix in _MARKDOWN_SUFFIXES:
                file_paths.append(dirpath / filename)

    logger.debug("files_discovered", count=len(file_paths), root=str(root))

    yield from file_paths
