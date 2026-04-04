# Matterify

Extract and aggregate YAML frontmatter from Markdown files.

[![Python version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python utility that recursively scans directory structures for Markdown files, extracts their embedded YAML frontmatter metadata, and aggregates all information into a structured format for further processing.

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
    extract_frontmatter,
    aggregate_frontmatter,
    export_json,
    iter_markdown_files,
)
```

#### extract_frontmatter

Extract YAML frontmatter from a single Markdown file.

```python
from pathlib import Path
from matterify import extract_frontmatter

entry = extract_frontmatter(Path("readme.md"))
print(entry.file_path)   # "readme.md"
print(entry.frontmatter) # {"title": "Read Me", ...}
print(entry.status)      # "ok" or "illegal"
```

#### aggregate_frontmatter

Scan directory and aggregate frontmatter using parallel workers.

```python
from pathlib import Path
from matterify import aggregate_frontmatter

result = aggregate_frontmatter(Path("./docs"))

# Returns a dictionary with metadata and files keys:
# {
#     "metadata": {
#         "source_directory": str,
#         "total_files": int,
#         "files_with_frontmatter": int,
#         "files_without_frontmatter": int,
#         "errors": int,
#         "scan_duration_seconds": float,
#         "avg_duration_per_file_ms": float,
#     },
#     "files": [
#         {
#             "file_path": str,
#             "frontmatter": dict | None,
#             "status": str,
#             "error": str | None,
#         },
#         ...
#     ]
# }
```

#### export_json

Serialize aggregated result to JSON file.

```python
from pathlib import Path
from matterify import _aggregate_dataclass, export_json

result = _aggregate_dataclass(Path("./docs"))
output_path = export_json(result, Path("output.json"))
print(output_path)  # Path to the written JSON file
```

#### iter_markdown_files

Yield Markdown files in directory.

```python
from pathlib import Path
from matterify import iter_markdown_files, BLACKLIST

# Using default blacklist
for md_file in iter_markdown_files(Path("./docs")):
    print(md_file)

# With custom blacklist
for md_file in iter_markdown_files(Path("./docs"), blacklist=(".git", "__pycache__")):
    print(md_file)
```

### Public Types

```python
from matterify import (
    FrontmatterEntry,
    ScanMetadata,
    AggregatedResult,
    BLACKLIST,
)

# FrontmatterEntry: extracted frontmatter from a single file
entry: FrontmatterEntry

# ScanMetadata: summary statistics about a scan
metadata: ScanMetadata

# AggregatedResult: holds metadata and file entries
result: AggregatedResult

# BLACKLIST: tuple of excluded directory names
print(BLACKLIST)  # (".git", ".obsidian", ...)
```

## JSON Output Structure

When using CLI with `--output` or calling `aggregate_frontmatter()`:

```json
{
  "metadata": {
    "source_directory": "/path/to/docs",
    "total_files": 10,
    "files_with_frontmatter": 8,
    "files_without_frontmatter": 2,
    "errors": 0,
    "scan_duration_seconds": 0.523,
    "avg_duration_per_file_ms": 52.3
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
      "error": null
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
