"""Frontmatter extraction and aggregation logic."""

import asyncio
import json
from pathlib import Path
from typing import Any

import yaml
from structlog import get_logger

logger = get_logger(__name__)

type FrontmatterDict = dict[str, Any]
type FileEntry = dict[str, Any]
type AggregatedResult = dict[str, Any]


async def extract_frontmatter(file_path: Path) -> FrontmatterDict | None:
    """Extract YAML frontmatter from a Markdown file.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        Parsed frontmatter as a dictionary, or None if no frontmatter found.
    """
    content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
    content = content.strip()

    if not content.startswith("---"):
        logger.debug("no_frontmatter", file=str(file_path))
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        logger.debug("invalid_frontmatter", file=str(file_path))
        return None

    yaml_block = parts[1]
    try:
        data = yaml.safe_load(yaml_block)
        if not isinstance(data, dict):
            logger.debug("non_dict_frontmatter", file=str(file_path))
            return None
        logger.debug("extracted_frontmatter", file=str(file_path))
        return data
    except yaml.YAMLError as exc:
        logger.warning("yaml_parse_error", file=str(file_path), error=str(exc))
        return None


async def scan_markdown_files(directory: Path) -> list[Path]:
    """Recursively find all Markdown files in a directory.

    Args:
        directory: Root directory to scan.

    Returns:
        Sorted list of Markdown file paths.
    """

    def _scan() -> list[Path]:
        return sorted(
            p for p in directory.rglob("*") if p.is_file() and p.suffix in {".md", ".markdown"}
        )

    files = await asyncio.to_thread(_scan)
    logger.debug("scanned_markdown_files", directory=str(directory), count=len(files))
    return files


async def aggregate_frontmatter(
    directory: Path,
) -> AggregatedResult:
    """Scan directory and aggregate all frontmatter into a structured result.

    Args:
        directory: Root directory to scan for Markdown files.

    Returns:
        Dictionary containing aggregated frontmatter data with metadata
        about the scan operation.
    """
    files = await scan_markdown_files(directory)
    results: list[FileEntry] = []
    errors: list[dict[str, str]] = []

    for file_path in files:
        try:
            frontmatter = await extract_frontmatter(file_path)
            relative_path = str(file_path.relative_to(directory))
            entry: FileEntry = {
                "file": relative_path,
                "frontmatter": frontmatter,
            }
            results.append(entry)
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
            logger.error("file_processing_error", file=str(file_path), error=str(exc))

    result: AggregatedResult = {
        "metadata": {
            "source_directory": str(directory),
            "total_files": len(files),
            "files_with_frontmatter": sum(1 for r in results if r["frontmatter"] is not None),
            "errors": len(errors),
        },
        "files": results,
    }

    if errors:
        result["errors"] = errors

    logger.info(
        "aggregation_complete",
        total_files=len(files),
        with_frontmatter=result["metadata"]["files_with_frontmatter"],
        errors=len(errors),
    )
    return result


async def export_json(
    directory: Path,
    output: Path,
) -> Path:
    """Aggregate frontmatter and export to a JSON file.

    Args:
        directory: Root directory to scan for Markdown files.
        output: Destination path for the JSON output file.

    Returns:
        Path to the written JSON file.
    """
    result = await aggregate_frontmatter(directory)
    json_content = json.dumps(result, indent=2, ensure_ascii=False)
    await asyncio.to_thread(output.write_text, json_content, encoding="utf-8")
    logger.info("json_exported", output=str(output))
    return output
