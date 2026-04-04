# Matterify

Extract and aggregate YAML frontmatter from Markdown files.

[![Python version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/matterify.svg)](https://pypi.org/project/matterify/)

## Quick Start

```bash
pip install matterify
matterify ./docs -o output.json
```

## Installation

```bash
# Using uv (recommended)
uv add matterify

# Or with pip
pip install matterify
```

## CLI Usage

```bash
matterify DIRECTORY [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Write JSON to file instead of stdout (if omitted, outputs to stdout)
- `-n-procs INT` - Worker process count (default: auto-detect CPU cores)
- `-v, --verbose` - Show progress and summary
- `-e, --exclude TEXT` - Additional directories to exclude

**Examples:**

```bash
# Output to stdout (JSON)
matterify ./docs

# Output to file
matterify ./docs -o output.json

# Verbose output
matterify ./docs --verbose
```

## Python API

### Public Functions

```python
from pathlib import Path
from matterify import (
    scan_directory,
)
```

#### scan_directory

Scan directory and aggregate frontmatter using parallel workers. Returns an `AggregatedResult` dataclass.

```python
from pathlib import Path
from matterify import scan_directory

result = scan_directory(Path("./docs"))

# AggregatedResult contains:
# - result.metadata: ScanMetadata with scan statistics
# - result.files: list[FrontmatterEntry] with extraction results

# Access metadata
print(result.metadata.total_files)
print(result.metadata.files_with_frontmatter)
print(result.metadata.scan_duration_seconds)

# Access files
for entry in result.files:
    print(entry.file_path, entry.status)

# Output to JSON file
import json
output = {
    "metadata": {
        "source_directory": result.metadata.source_directory,
        "total_files": result.metadata.total_files,
        "files_with_frontmatter": result.metadata.files_with_frontmatter,
        "files_without_frontmatter": result.metadata.files_without_frontmatter,
        "errors": result.metadata.errors,
        "scan_duration_seconds": result.metadata.scan_duration_seconds,
        "avg_duration_per_file_ms": result.metadata.avg_duration_per_file_ms,
        "throughput_files_per_second": result.metadata.throughput_files_per_second,
    },
    "files": [
        {
            "file_path": e.file_path,
            "frontmatter": e.frontmatter,
            "status": e.status,
            "error": e.error,
            "file_size": e.file_size,
            "modified_time": e.modified_time,
            "access_time": e.access_time,
        }
        for e in result.files
    ],
}
Path("output.json").write_text(json.dumps(output, indent=2))
```

### Public Types

```python
from matterify import (
    FrontmatterEntry,
    ScanMetadata,
    AggregatedResult,
)

# FrontmatterEntry: extracted frontmatter from a single file
entry: FrontmatterEntry

# ScanMetadata: summary statistics about a scan
metadata: ScanMetadata

# AggregatedResult: holds metadata and file entries
result: AggregatedResult
```

## JSON Output Structure

When using CLI with `--output`:

```json
{
  "metadata": {
    "source_directory": "/path/to/docs",
    "total_files": 10,
    "files_with_frontmatter": 8,
    "files_without_frontmatter": 2,
    "errors": 0,
    "scan_duration_seconds": 0.523,
    "avg_duration_per_file_ms": 52.3,
    "throughput_files_per_second": 19.1
  },
  "files": [
    {
      "file_path": "docs/getting-started.md",
      "frontmatter": {
        "title": "Getting Started",
        "date": "2024-01-15",
        "tags": ["guide", "tutorial"]
      },
      "status": "ok",
      "error": null,
      "file_size": 1234,
      "modified_time": "2024-01-15T10:30:00",
      "access_time": "2024-01-15T10:30:00"
    }
  ]
}
```

## Default Exclusions

The following directories are excluded from scanning by default:

- `.git`
- `.obsidian`
- `__pycache__`
- `.venv`
- `venv`
- `node_modules`
- `.mypy_cache`
- `.pytest_cache`
- `.ruff_cache`

Use `-e` or `--exclude` to add custom exclusions.

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format and lint
uv run ruff format src/ tests/
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
