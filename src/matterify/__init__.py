"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

__version__ = "0.1.0"

from matterify.extractor import aggregate_frontmatter, export_json, extract_frontmatter
from matterify.models import AggregatedResult, FrontmatterEntry, ScanMetadata
from matterify.scanner import BLACKLIST, iter_markdown_files

__all__ = [
    "BLACKLIST",
    "AggregatedResult",
    "FrontmatterEntry",
    "ScanMetadata",
    "__version__",
    "aggregate_frontmatter",
    "export_json",
    "extract_frontmatter",
    "iter_markdown_files",
]
