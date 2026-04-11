"""Dataclass definitions for frontmatter extraction results."""

from dataclasses import dataclass
from pathlib import Path

from matterify.enums import FileError, FileStatus


@dataclass(frozen=True)
class FileStats:
    """Encapsulates file statistics (size and timestamps).

    Attributes:
        file_size: File size in bytes, or None if unavailable.
        modified_time: Last modification time as ISO 8601 string, or None.
        access_time: Last access time as ISO 8601 string, or None.
    """

    file_size: int | None = None
    modified_time: str | None = None
    access_time: str | None = None


@dataclass(frozen=True)
class FileEntry:
    """Represents extracted frontmatter from a single Markdown file.

    Attributes:
        file_path: Relative path to the scanned directory.
        frontmatter: Parsed YAML content as a dictionary.
        status: Processing status - FileStatus.OK or FileStatus.ILLEGAL.
        error: Error code if status is FileStatus.ILLEGAL.
        stats: File statistics (size and timestamps).
        file_hash: SHA-256 hash of file content, or None if not computed.
        custom_data: Custom data injected by callback function, or None if no callback provided.
    """

    file_path: Path
    frontmatter: dict[str, object] | None
    status: FileStatus
    error: FileError | None
    stats: FileStats | None = None
    file_hash: str | None = None
    custom_data: object | None = None


@dataclass(frozen=True)
class ScanMetadata:
    """Summary statistics about a scan operation.

    Attributes:
        root: Absolute path to the scanned directory.
        total_files: Total number of Markdown files discovered.
        files_with_frontmatter: Count of files with valid frontmatter.
        files_without_frontmatter: Count of files without frontmatter.
        errors: Count of files that produced errors.
        scan_duration_seconds: Total time taken for the scan.
        avg_duration_per_file_ms: Average processing time per file.
        throughput_files_per_second: Number of files processed per second.
    """

    root: Path
    total_files: int
    files_with_frontmatter: int | None
    files_without_frontmatter: int | None
    errors: int
    scan_duration_seconds: float
    avg_duration_per_file_ms: float
    throughput_files_per_second: float


@dataclass(frozen=True)
class ScanResults:
    """Final output structure containing all scan results.

    Attributes:
        metadata: Summary statistics about the scan.
        files: List of individual file extraction results.
    """

    metadata: ScanMetadata
    files: list[FileEntry]
