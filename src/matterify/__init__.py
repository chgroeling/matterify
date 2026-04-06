"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

from importlib.metadata import version

__version__ = version("matterify")

from matterify.extractor import (
    scan_directory as scan_directory,
)
from matterify.models import (
    FileEntry as FileEntry,
)
from matterify.models import (
    ScanMetadata as ScanMetadata,
)
from matterify.models import (
    ScanResults as ScanResults,
)
