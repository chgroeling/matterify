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
- `--n-procs INT` - Worker process count (default: auto-detect CPU cores)
- `-v, --verbose` - Show progress and summary
- `-e, --exclude TEXT` - Additional directories to exclude
- `--hash / --no-hash` - Enable/disable SHA-256 hash computation
- `--stats / --no-stats` - Enable/disable file statistics (size, modified time, access time)
- `--debug` - Enable debug logging
- `--version` - Show version information and exit

**Examples:**

```bash
# Output to stdout (JSON)
matterify ./docs

# Output to file
matterify ./docs -o output.json

# Verbose output
matterify ./docs --verbose

# Disable hashes and file stats
matterify ./docs --no-hash --no-stats

# Exclude additional directories
matterify ./docs -e build -e .cache
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
# - result.files: list of file entries with extraction results

# Access metadata
print(result.metadata.total_files)
print(result.metadata.files_with_frontmatter)
print(result.metadata.scan_duration_seconds)

# Access files
for entry in result.files:
    print(entry.file_path, entry.status)
    print(entry.stats.file_size if entry.stats else None)
```

### Public Types

```python
from matterify import (
    FileEntry,
    ScanMetadata,
    AggregatedResult,
)

# FileEntry: extracted frontmatter from a single file
entry: FileEntry

# ScanMetadata: summary statistics about a scan
metadata: ScanMetadata

# AggregatedResult: holds metadata and file entries
result: AggregatedResult
```

## JSON Output Structure

When using CLI (stdout or `--output`), the payload has this shape:

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
      "file_path": "getting-started.md",
      "frontmatter": {
        "title": "Getting Started",
        "date": "2024-01-15",
        "tags": ["guide", "tutorial"]
      },
      "status": "ok",
      "error": null,
      "stats": {
        "file_size": 1234,
        "modified_time": "2024-01-15T10:30:00",
        "access_time": "2024-01-15T10:30:00"
      },
      "file_hash": "abc123..."
    }
  ]
}
```

`status` is either `"ok"` or `"illegal"`.

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
