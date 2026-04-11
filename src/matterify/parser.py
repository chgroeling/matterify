"""YAML frontmatter parsing logic."""

from datetime import date, datetime
from pathlib import Path
from typing import cast

import yaml

from matterify.enums import FileError, FileStatus


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
    file_path: Path,
) -> tuple[Path, dict[str, object] | None, FileStatus, FileError | None]:
    """Extract and validate YAML frontmatter from file content.

    Args:
        content: The file content as a string.
        file_path: The file path for the entry.

    Returns:
        Tuple of (file_path, frontmatter, status, error).
    """
    content = content.strip()

    if not content.startswith("---"):
        return (file_path, None, FileStatus.ILLEGAL, FileError.NO_FRONTMATTER)

    parts = content.split("---", 2)
    if len(parts) < 3:
        return (file_path, None, FileStatus.ILLEGAL, FileError.NO_FRONTMATTER)

    yaml_block = parts[1]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return (file_path, None, FileStatus.ILLEGAL, FileError.YAML_PARSE_ERROR)

    if not isinstance(data, dict):
        return (file_path, None, FileStatus.ILLEGAL, FileError.NON_DICT_FRONTMATTER)

    data = _serialize_datetime(data)
    serialized = cast("dict[str, object] | None", data)

    return (file_path, serialized, FileStatus.OK, None)
