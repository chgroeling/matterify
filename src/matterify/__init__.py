"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

__version__ = "0.1.0"

from matterify.extractor import (
    DEFAULT_N_PROCS,
    extract_frontmatter,
    scan_directory,
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
    "extract_frontmatter",
    "iter_markdown_files",
    "scan_directory",
]
