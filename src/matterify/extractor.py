"""Frontmatter extraction and aggregation logic."""

import hashlib
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict, cast

import yaml
from structlog import get_logger

from matterify.constants import DEFAULT_N_PROCS
from matterify.models import AggregatedResult, FrontmatterEntry, ScanMetadata

logger = get_logger(__name__)


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


def _extract_frontmatter(file_path: Path) -> FrontmatterEntry:
    """Extract and validate YAML frontmatter from a Markdown file.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        FrontmatterEntry with status "ok" or "illegal".
    """
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        return FrontmatterEntry(
            file_path=str(file_path),
            frontmatter=None,
            status="illegal",
            error=str(exc),
        )

    if not content.startswith("---"):
        return FrontmatterEntry(
            file_path=str(file_path),
            frontmatter=None,
            status="illegal",
            error="no_frontmatter",
        )

    parts = content.split("---", 2)
    if len(parts) < 3:
        return FrontmatterEntry(
            file_path=str(file_path),
            frontmatter=None,
            status="illegal",
            error="no_frontmatter",
        )

    yaml_block = parts[1]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return FrontmatterEntry(
            file_path=str(file_path),
            frontmatter=None,
            status="illegal",
            error="yaml_parse_error",
        )

    if not isinstance(data, dict):
        return FrontmatterEntry(
            file_path=str(file_path),
            frontmatter=None,
            status="illegal",
            error="non_dict_frontmatter",
        )

    data = _serialize_datetime(data)
    serialized = cast("dict[str, object] | None", data)

    return FrontmatterEntry(
        file_path=str(file_path),
        frontmatter=serialized,
        status="ok",
        error=None,
    )


class _FileStats(TypedDict):
    file_size: int | None
    modified_time: str | None
    access_time: str | None


def _get_file_stats(file_path: Path) -> _FileStats:
    """Get file statistics (size, modified time, access time).

    Args:
        file_path: Path to the file.

    Returns:
        Dictionary with file_size, modified_time, access_time.
    """
    file_size: int | None = None
    modified_time: str | None = None
    access_time: str | None = None

    try:
        stat_info = file_path.stat()
        file_size = stat_info.st_size
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        access_time = datetime.fromtimestamp(stat_info.st_atime).isoformat()
    except OSError:
        pass

    return {
        "file_size": file_size,
        "modified_time": modified_time,
        "access_time": access_time,
    }


def _compute_file_hash(file_path: Path) -> str | None:
    """Compute SHA-256 hash of file content.

    Args:
        file_path: Path to the file.

    Returns:
        Hex string of SHA-256 hash, or None on error.
    """
    try:
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None


def _worker_extract(root_str: str, file_str: str) -> FrontmatterEntry:
    """Worker function for ProcessPoolExecutor.

    Args:
        root_str: Root directory as string (unused, kept for future extension).
        file_str: Absolute file path as string.

    Returns:
        FrontmatterEntry for the given file.
    """
    return _extract_frontmatter(Path(file_str))


def scan_directory(
    directory: Path,
    n_procs: int | None = None,
    blacklist: tuple[str, ...] | None = None,
    compute_hash: bool = False,
) -> AggregatedResult:
    """Scan directory and aggregate frontmatter using concurrent workers.

    Args:
        directory: Root directory to scan.
        n_procs: Worker process count (default: auto-detect CPU cores, capped at file count).
        blacklist: Directory names to exclude from traversal.
        compute_hash: Whether to compute SHA-256 hash for each file (default: False).

    Returns:
        AggregatedResult with metadata and file entries.

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
    from matterify.constants import BLACKLIST
    from matterify.scanner import iter_markdown_files

    effective_blacklist = blacklist if blacklist is not None else BLACKLIST
    effective_n_procs = os.cpu_count() or DEFAULT_N_PROCS

    logger.debug(
        "starting_scan",
        directory=str(directory),
        blacklist=effective_blacklist,
        n_procs=effective_n_procs,
    )

    start_time = time.perf_counter()
    file_paths = list(iter_markdown_files(directory, blacklist=effective_blacklist))
    total_files = len(file_paths)

    logger.debug("files_discovered", count=total_files, directory=str(directory))

    if total_files == 0:
        duration = time.perf_counter() - start_time
        metadata = ScanMetadata(
            source_directory=str(directory),
            total_files=0,
            files_with_frontmatter=0,
            files_without_frontmatter=0,
            errors=0,
            scan_duration_seconds=round(duration, 3),
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        )
        return AggregatedResult(metadata=metadata, files=[])

    max_workers = min(total_files, effective_n_procs)
    logger.debug("worker_pool_initialized", max_workers=max_workers)

    results: list[FrontmatterEntry] = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(_worker_extract, str(directory), str(fp)): fp for fp in file_paths
        }
        for future in as_completed(future_to_path):
            entry = future.result()
            try:
                rel_path = str(Path(entry.file_path).relative_to(directory))
            except ValueError:
                rel_path = entry.file_path

            file_path = Path(entry.file_path)
            stats = _get_file_stats(file_path)
            file_hash: str | None = None
            if compute_hash:
                file_hash = _compute_file_hash(file_path)

            results.append(
                FrontmatterEntry(
                    file_path=rel_path,
                    frontmatter=entry.frontmatter,
                    status=entry.status,
                    error=entry.error,
                    file_size=stats["file_size"],
                    modified_time=stats["modified_time"],
                    access_time=stats["access_time"],
                    file_hash=file_hash,
                )
            )

    results.sort(key=lambda e: e.file_path)

    files_with_fm = sum(1 for r in results if r.status == "ok")
    files_without_fm = sum(
        1 for r in results if r.status == "illegal" and r.error == "no_frontmatter"
    )
    errors = sum(1 for r in results if r.status == "illegal" and r.error != "no_frontmatter")

    duration = time.perf_counter() - start_time
    avg_ms = (duration / total_files * 1000) if total_files > 0 else 0.0
    throughput = (total_files / duration) if duration > 0 else 0.0

    metadata = ScanMetadata(
        source_directory=str(directory),
        total_files=total_files,
        files_with_frontmatter=files_with_fm,
        files_without_frontmatter=files_without_fm,
        errors=errors,
        scan_duration_seconds=round(duration, 3),
        avg_duration_per_file_ms=round(avg_ms, 1),
        throughput_files_per_second=round(throughput, 1),
    )

    logger.info(
        "aggregation_complete",
        total_files=total_files,
        with_frontmatter=files_with_fm,
        errors=errors,
        duration=round(duration, 3),
        n_procs=effective_n_procs,
        throughput=round(throughput, 1),
    )

    return AggregatedResult(metadata=metadata, files=results)
