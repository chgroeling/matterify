"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

__version__ = "0.1.0"

from matterify.extractor import (
    scan_directory as scan_directory,
)
from matterify.models import (
    AggregatedResult as AggregatedResult,
)
from matterify.models import (
    FileEntry as FileEntry,
)
from matterify.models import (
    ScanMetadata as ScanMetadata,
)
