"""Matterify - Extract and aggregate YAML frontmatter from Markdown files."""

from importlib.metadata import version

__version__ = version("matterify")

from matterify.core import scan_directory as scan_directory
from matterify.enums import FileError as FileError
from matterify.enums import FileStatus as FileStatus
from matterify.models import (
    FileEntry as FileEntry,
)
from matterify.models import (
    ScanMetadata as ScanMetadata,
)
from matterify.models import (
    ScanResults as ScanResults,
)
from matterify.types import ContentCallback as ContentCallback
