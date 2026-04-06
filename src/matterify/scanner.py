"""Directory traversal with blacklist filtering."""

from collections.abc import Iterable
from pathlib import Path

from structlog import get_logger

from matterify.constants import BLACKLIST

logger = get_logger(__name__)

_MARKDOWN_SUFFIXES = {".md", ".markdown"}


def iter_markdown_files(
    root: Path,
    exclude: tuple[str, ...] = BLACKLIST,
) -> Iterable[Path]:
    """Yield relative paths to Markdown files under root.

    Recursively walks the directory tree, pruning excluded directories
    in-place to avoid unnecessary I/O.

    Args:
        root: Root directory to scan.
        exclude: Directory names to exclude from traversal.

    Yields:
        Relative paths to discovered Markdown files.
    """
    logger.debug("starting_directory_traversal", root=str(root), exclude=exclude)

    exclude_set = set(exclude)
    discovered_count = 0

    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in exclude_set]
        for filename in filenames:
            suffix = Path(filename).suffix.lower()
            if suffix in _MARKDOWN_SUFFIXES:
                discovered_count += 1
                yield (dirpath / filename).relative_to(root)

    logger.debug("files_discovered", count=discovered_count, root=str(root))
