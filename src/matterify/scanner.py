"""Directory traversal with glob-based exclusion filtering."""

import fnmatch
import re
from collections.abc import Iterable
from pathlib import Path

from structlog import get_logger

from matterify.constants import DEFAULT_EXCLUDE_PATTERNS

logger = get_logger(__name__)

_MARKDOWN_SUFFIXES = {".md", ".markdown"}


class _GlobMatcher:
    """Pre-compiled glob matcher for efficient pattern matching."""

    __slots__ = ("_regex",)

    def __init__(self, patterns: tuple[str, ...]) -> None:
        self._regex = re.compile(
            "|".join(fnmatch.translate(p) for p in patterns),
        )

    def matches(self, path: Path) -> bool:
        return self._regex.match(path.as_posix()) is not None


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
    dir_matcher = _GlobMatcher(exclude)
    file_matcher = _GlobMatcher(exclude)

    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if not dir_matcher.matches(dirpath / d)]
        for filename in filenames:
            filepath = dirpath / filename
            if file_matcher.matches(filepath):
                continue
            suffix = Path(filename).suffix.lower()
            if suffix in _MARKDOWN_SUFFIXES:
                discovered_count += 1
                yield filepath.relative_to(root)

    logger.debug("files_discovered", count=discovered_count, root=str(root))
