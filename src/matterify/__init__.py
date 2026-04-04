"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

__version__ = "0.1.0"

from matterify.extractor import (
    DEFAULT_N_PROCS,
    _aggregate_dataclass,
    aggregate_frontmatter,
    extract_frontmatter,
)
from matterify.models import AggregatedResult, FrontmatterEntry, ScanMetadata
from matterify.scanner import BLACKLIST, iter_markdown_files

__all__ = [
    "BLACKLIST",
    "DEFAULT_N_PROCS",
    "AggregatedResult",
    "FrontmatterEntry",
    "ScanMetadata",
    "__version__",
    "_aggregate_dataclass",
    "aggregate_frontmatter",
    "extract_frontmatter",
    "iter_markdown_files",
]
