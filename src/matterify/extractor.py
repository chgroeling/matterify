"""Frontmatter extraction and aggregation logic."""

import hashlib
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from typing import cast

import yaml
from structlog import get_logger

from matterify.constants import BLACKLIST, DEFAULT_N_PROCS
from matterify.models import FileEntry, FileStats, ScanMetadata, ScanResults
from matterify.scanner import iter_markdown_files

logger = get_logger(__name__)

__all__ = ["scan_directory"]

type ContentCallback = Callable[[str], dict[str, object] | None]


def _serialize_datetime(
    value: dict[str, object] | list[object] | object,
) -> dict[str, object] | list[object] | object:
    """Recursively convert datetime/date objects to ISO strings."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_datetime(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_datetime(item) for item in value]
    return value


def _extract_frontmatter_from_content(
    content: str,
    file_path_str: str,
) -> tuple[str, dict[str, object] | None, str, str | None]:
    """Extract and validate YAML frontmatter from file content.

    Args:
        content: The file content as a string.
        file_path_str: The file path as a string for the entry.

    Returns:
        Tuple of (file_path, frontmatter, status, error).
    """
    content = content.strip()

    if not content.startswith("---"):
        return (file_path_str, None, "illegal", "no_frontmatter")

    parts = content.split("---", 2)
    if len(parts) < 3:
        return (file_path_str, None, "illegal", "no_frontmatter")

    yaml_block = parts[1]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return (file_path_str, None, "illegal", "yaml_parse_error")

    if not isinstance(data, dict):
        return (file_path_str, None, "illegal", "non_dict_frontmatter")

    data = _serialize_datetime(data)
    serialized = cast("dict[str, object] | None", data)

    return (file_path_str, serialized, "ok", None)


def _compute_file_hash(content: bytes) -> str | None:
    """Compute SHA-256 hash of file content.

    Args:
        content: The file content as bytes.

    Returns:
        Hex string of SHA-256 hash, or None on error.
    """
    try:
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None


def _worker_extract(
    root_str: str,
    file_str: str,
    compute_hash: bool,
    compute_stats: bool,
    compute_frontmatter: bool,
    callback: ContentCallback | None = None,
) -> FileEntry:
    """Worker function for ProcessPoolExecutor.

    Reads the file only when needed for hash or frontmatter extraction.

    Args:
        root_str: Root directory as string.
        file_str: Relative file path as string.
        compute_hash: Whether to compute SHA-256 hash.
        compute_stats: Whether to compute file statistics.
        compute_frontmatter: Whether to extract YAML frontmatter.
        callback: Optional callable that receives file content and returns custom data dict.
            Must be picklable (module-level function, not lambda or closure).

    Returns:
        Fully populated FileEntry for the given file.
    """
    file_path = Path(root_str) / file_str

    file_stats: FileStats | None = None
    file_hash: str | None = None
    frontmatter: dict[str, object] | None = None
    custom_data: dict[str, object] | None = None
    status: str
    error: str | None
    fm_file_path = file_str

    if compute_stats:
        try:
            stat_info = file_path.stat()
            file_stats = FileStats(
                file_size=stat_info.st_size,
                modified_time=datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                access_time=datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            )
        except OSError:
            pass

    if compute_frontmatter or compute_hash or callback is not None:
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as exc:
            return FileEntry(
                file_path=file_str,
                frontmatter=None,
                status="illegal",
                error=str(exc),
            )

        if compute_frontmatter or callback is not None:
            content = raw_bytes.decode("utf-8")

            if compute_frontmatter:
                fm_file_path, frontmatter, status, error = _extract_frontmatter_from_content(
                    content, file_str
                )
            else:
                status = "ok"
                error = None

            if callback is not None:
                custom_data = callback(content)
        else:
            status = "ok"
            error = None

        if compute_hash:
            file_hash = _compute_file_hash(raw_bytes)
    else:
        status = "ok"
        error = None

    return FileEntry(
        file_path=fm_file_path,
        frontmatter=frontmatter,
        status=status,
        error=error,
        stats=file_stats,
        file_hash=file_hash,
        custom_data=custom_data,
    )


def scan_directory(
    root: Path,
    n_procs: int | None = None,
    exclude: tuple[str, ...] | None = None,
    compute_hash: bool = True,
    compute_stats: bool = True,
    compute_frontmatter: bool = True,
    callback: ContentCallback | None = None,
) -> ScanResults:
    """Scan directory and aggregate frontmatter using concurrent workers.

    Args:
        root: Root directory to scan.
        n_procs: Worker process count (default: auto-detect CPU cores, capped at file count).
        exclude: Directory names to exclude from traversal.
        compute_hash: Whether to compute SHA-256 hash for each file (default: True).
        compute_stats: Whether to compute file stats (size, mtime, atime) (default: True).
        compute_frontmatter: Whether to extract YAML frontmatter (default: True).
        callback: Optional callable that receives file content and returns custom data dict.
            Must be picklable (module-level function, not lambda or closure).

    Returns:
        ScanResults with metadata and file entries.

    Example:
        ```python
        >>> from pathlib import Path
        >>> result = scan_directory(Path("./docs"))
        >>> result.metadata.total_files
        5
        >>> result.files[0].file_path
        'getting-started.md'
        >>> result.files[0].frontmatter
        {'title': 'Getting Started', 'version': '1.0.0'}
        ```
    """

    start_time = time.perf_counter()

    effective_exclude = exclude if exclude is not None else BLACKLIST
    effective_n_procs = n_procs if n_procs is not None else os.cpu_count()
    effective_n_procs = effective_n_procs if effective_n_procs is not None else DEFAULT_N_PROCS

    logger.debug(
        "starting_scan",
        root=str(root),
        exclude=effective_exclude,
        n_procs=effective_n_procs,
    )

    file_paths = list(iter_markdown_files(root, exclude=effective_exclude))
    total_files = len(file_paths)

    if total_files == 0:
        duration = time.perf_counter() - start_time
        fm_none = None if not compute_frontmatter else 0
        metadata = ScanMetadata(
            root=str(root),
            total_files=0,
            files_with_frontmatter=fm_none,
            files_without_frontmatter=fm_none,
            errors=0,
            scan_duration_seconds=round(duration, 3),
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        )
        result = ScanResults(metadata=metadata, files=[])
        return result

    if not compute_frontmatter and not compute_hash and not compute_stats:
        duration = time.perf_counter() - start_time
        metadata = ScanMetadata(
            root=str(root),
            total_files=total_files,
            files_with_frontmatter=None,
            files_without_frontmatter=None,
            errors=0,
            scan_duration_seconds=round(duration, 3),
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        )
        result = ScanResults(metadata=metadata, files=[])
        return result

    max_workers = min(total_files, effective_n_procs)
    logger.debug("worker_pool_initialized", max_workers=max_workers)

    results: list[FileEntry] = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(
                _worker_extract,
                str(root),
                str(fp),
                compute_hash,
                compute_stats,
                compute_frontmatter,
                callback,
            ): fp
            for fp in file_paths
        }
        for future in as_completed(future_to_path):
            entry = future.result()
            results.append(entry)

    results.sort(key=lambda e: e.file_path)

    if compute_frontmatter:
        files_with_fm = sum(1 for r in results if r.frontmatter is not None)
        files_without_fm = sum(
            1 for r in results if r.status == "illegal" and r.error == "no_frontmatter"
        )
    else:
        files_with_fm = None
        files_without_fm = None
    errors = sum(1 for r in results if r.status == "illegal" and r.error != "no_frontmatter")

    duration = time.perf_counter() - start_time
    avg_ms = (duration / total_files * 1000) if total_files > 0 else 0.0
    throughput = (total_files / duration) if duration > 0 else 0.0

    metadata = ScanMetadata(
        root=str(root),
        total_files=total_files,
        files_with_frontmatter=files_with_fm,
        files_without_frontmatter=files_without_fm,
        errors=errors,
        scan_duration_seconds=round(duration, 3),
        avg_duration_per_file_ms=round(avg_ms, 1),
        throughput_files_per_second=round(throughput, 1),
    )

    logger.info(
        "scan_complete",
        total_files=total_files,
        with_frontmatter=files_with_fm,
        errors=errors,
        duration=round(duration, 3),
        n_procs=effective_n_procs,
        throughput=round(throughput, 1),
    )

    result = ScanResults(metadata=metadata, files=results)

    return result
