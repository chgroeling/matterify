# Matterify

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)
[![PyPI](https://img.shields.io/pypi/v/matterify.svg)](https://pypi.org/project/matterify/)

Extract and aggregate YAML frontmatter from Markdown files, with optional SHA-256 hashes
and file statistics.

## Features

- Recursive Markdown discovery with configurable directory exclusions
- YAML frontmatter extraction with structured `ok`/`illegal` status reporting
- Optional SHA-256 file hashes and file stats (size, mtime, atime)
- Parallel scan workers for faster processing on larger vaults/projects

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

`DIRECTORY` must exist and is scanned recursively for `.md` and `.markdown` files.

**Options:**
- `--version` - Show version information and exit
- `--debug` - Enable debug logging
- `-o, --output PATH` - Write JSON to file instead of stdout (if omitted, outputs to stdout)
- `--n-procs INT` - Worker process count (default: auto-detect CPU cores)
- `-v, --verbose` - Show progress and summary
- `-e, --exclude TEXT` - Glob patterns to exclude (e.g., `**/.git`, `**/__pycache__`)
- `-i, --include PATH` - Additional file paths to include in scan (repeatable)
- `--hash / --no-hash` - Enable/disable SHA-256 hash computation
- `--stats / --no-stats` - Enable/disable file statistics (size, modified time, access time)
- `--frontmatter / --no-frontmatter` - Enable/disable YAML frontmatter extraction
- `--help` - Show command help and exit

When `--no-frontmatter` is used, metadata fields `files_with_frontmatter` and
`files_without_frontmatter` are `null`.

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

# Hash + stats only (skip YAML parsing)
matterify ./docs --no-frontmatter

# Exclude directories using glob patterns
matterify ./docs -e '**/build' -e '**/.cache'

# Include additional files (any extension)
matterify ./docs -i notes.txt -i ../shared/changelog.txt

# Full help
matterify --help
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

Scan directory and aggregate frontmatter using parallel workers. Returns a
`ScanResults` dataclass.

```python
from pathlib import Path
from matterify import scan_directory

result = scan_directory(Path("./docs"))

# ScanResults contains:
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

#### Custom data callback

You can pass a callback function to inject custom data into each file entry. The callback
receives the raw file content as a string and should return any value or `None`. The result
is stored in the `custom_data` field of each `FileEntry`.

```python
from pathlib import Path
from matterify import scan_directory

def count_words(content: str) -> object:
    return {"word_count": len(content.split())}

result = scan_directory(Path("./docs"), callback=count_words)

for entry in result.files:
    if entry.custom_data:
        print(entry.file_path, entry.custom_data["word_count"])
```

**Important:** The callback must be a module-level function (picklable for multiprocessing),
not a lambda or closure.

### Public Types

```python
from matterify import (
    FileEntry,
    ScanMetadata,
    ScanResults,
)

# FileEntry: extracted frontmatter from a single file
entry: FileEntry

# ScanMetadata: summary statistics about a scan
metadata: ScanMetadata

# ScanResults: holds metadata and file entries
result: ScanResults
```

## JSON Output Structure

When using CLI (stdout or `--output`), the payload has this shape:

```json
{
  "metadata": {
    "root": "/path/to/docs",
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

The following glob patterns are excluded from scanning by default:

- `**/.git` - Git repositories
- `**/.obsidian` - Obsidian vault settings
- `**/__pycache__` - Python bytecode cache
- `**/.venv` - Python virtual environments
- `**/venv` - Python virtual environments
- `**/node_modules` - Node.js dependencies
- `**/.mypy_cache` - MyPy type checker cache
- `**/.pytest_cache` - Pytest cache
- `**/.ruff_cache` - Ruff linter cache

The `**/` prefix matches directories at any depth. Use `-e` or `--exclude` to add custom exclusion patterns.

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
