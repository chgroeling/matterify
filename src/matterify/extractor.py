"""Frontmatter extraction and aggregation logic."""

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from typing import cast

import yaml
from structlog import get_logger

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


def extract_frontmatter(file_path: Path) -> FrontmatterEntry:
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


def _worker_extract(root_str: str, file_str: str) -> FrontmatterEntry:
    """Worker function for ProcessPoolExecutor.

    Args:
        root_str: Root directory as string (unused, kept for future extension).
        file_str: Absolute file path as string.

    Returns:
        FrontmatterEntry for the given file.
    """
    return extract_frontmatter(Path(file_str))


def aggregate_frontmatter(
    directory: Path,
    n_procs: int = 4,
) -> AggregatedResult:
    """Scan directory and aggregate frontmatter using concurrent workers.

    Args:
        directory: Root directory to scan.
        n_procs: Worker process count (capped at file count).

    Returns:
        AggregatedResult with metadata and file entries.
    """
    from matterify.scanner import iter_markdown_files

    start_time = time.perf_counter()
    file_paths = list(iter_markdown_files(directory))
    total_files = len(file_paths)

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
        )
        return AggregatedResult(metadata=metadata, files=[])

    max_workers = min(total_files, n_procs)
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
            results.append(
                FrontmatterEntry(
                    file_path=rel_path,
                    frontmatter=entry.frontmatter,
                    status=entry.status,
                    error=entry.error,
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

    metadata = ScanMetadata(
        source_directory=str(directory),
        total_files=total_files,
        files_with_frontmatter=files_with_fm,
        files_without_frontmatter=files_without_fm,
        errors=errors,
        scan_duration_seconds=round(duration, 3),
        avg_duration_per_file_ms=round(avg_ms, 1),
    )

    logger.info(
        "aggregation_complete",
        total_files=total_files,
        with_frontmatter=files_with_fm,
        errors=errors,
        duration=round(duration, 3),
    )

    return AggregatedResult(metadata=metadata, files=results)


def export_json(
    result: AggregatedResult,
    output: Path,
) -> Path:
    """Serialize AggregatedResult to JSON file.

    Args:
        result: Aggregated result to serialize.
        output: Destination path for the JSON output file.

    Returns:
        Path to the written file.
    """
    data = {
        "metadata": {
            "source_directory": result.metadata.source_directory,
            "total_files": result.metadata.total_files,
            "files_with_frontmatter": result.metadata.files_with_frontmatter,
            "files_without_frontmatter": result.metadata.files_without_frontmatter,
            "errors": result.metadata.errors,
            "scan_duration_seconds": result.metadata.scan_duration_seconds,
            "avg_duration_per_file_ms": result.metadata.avg_duration_per_file_ms,
        },
        "files": [
            {
                "file_path": entry.file_path,
                "frontmatter": entry.frontmatter,
                "status": entry.status,
                "error": entry.error,
            }
            for entry in result.files
        ],
    }
    json_content = json.dumps(data, indent=2, ensure_ascii=False)
    output.write_text(json_content, encoding="utf-8")
    logger.info("json_exported", output=str(output))
    return output
