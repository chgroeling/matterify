# Matterify Specification v0.1.0

## Overview
Matterify is a Python utility that recursively scans directory structures for Markdown files, extracts their embedded YAML frontmatter metadata, and aggregates all information into a structured, machine-readable JSON file for further processing.

This specification defines the first production version, incorporating proven design patterns from reference implementations (`nls.py`, `note_core.py`) including concurrent file processing, robust error handling, and clean data structures.

---

## Architecture

### Core Principles
1. **Separation of Concerns**: Extraction logic, file scanning, and CLI are strictly isolated
2. **Concurrent Processing**: Use `ProcessPoolExecutor` for CPU-bound YAML parsing across multiple files
3. **Fail-Safe Design**: Files with missing/invalid frontmatter produce "illegal" status entries, not crashes
4. **Structured Output**: All results use frozen dataclasses for immutability and type safety
5. **Blacklist Filtering**: Skip known non-content directories during traversal

### Module Structure
```
src/matterify/
├── __init__.py          # Version + public API
├── extractor.py         # Core extraction & aggregation logic
├── scanner.py           # Directory traversal with blacklist
├── models.py            # Dataclass definitions
├── cli.py               # Click CLI entry points
└── logging.py           # Debug & console config (existing)
```

---

## Data Models

### `FrontmatterEntry`
Represents successfully extracted frontmatter from a single file.

```python
@dataclass(frozen=True)
class FrontmatterEntry:
    file_path: str      # Relative path to scanned directory
    frontmatter: dict   # Parsed YAML content
    status: str         # "ok" | "illegal"
    error: str | None   # Error message if status == "illegal"
```

### `AggregatedResult`
Final output structure for JSON export.

```python
@dataclass(frozen=True)
class AggregatedResult:
    metadata: ScanMetadata
    files: list[FrontmatterEntry]
```

### `ScanMetadata`
Summary statistics about the scan operation.

```python
@dataclass(frozen=True)
class ScanMetadata:
    source_directory: str
    total_files: int
    files_with_frontmatter: int
    files_without_frontmatter: int
    errors: int
    scan_duration_seconds: float
    avg_duration_per_file_ms: float
```

---

## Core Components

### 1. File Scanner (`scanner.py`)

**Purpose**: Recursively find Markdown files while honoring blacklist rules.

**Key Design**:
- Use `os.walk()` for efficient directory traversal
- Prune blacklisted directories in-place during walk (avoids unnecessary I/O)
- Support configurable blacklist patterns

**Default Blacklist**:
```python
BLACKLIST: tuple[str, ...] = (
    ".git",
    ".obsidian",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
)
```

**Public API**:
```python
def iter_markdown_files(
    root: Path,
    blacklist: tuple[str, ...] = BLACKLIST,
) -> Iterable[Path]:
    """Yield absolute paths to Markdown files under root."""
```

### 2. Frontmatter Extractor (`extractor.py`)

**Purpose**: Parse YAML frontmatter from individual Markdown files.

**Extraction Logic**:
1. Read file content
2. Check for `---` delimiter at start
3. Split on second `---` to isolate YAML block
4. Parse with `yaml.safe_load()`
5. Validate result is a dictionary

**Error Handling**:
- Missing frontmatter → `status="illegal"`, `error="no_frontmatter"`
- Invalid YAML → `status="illegal"`, `error="yaml_parse_error"`
- Non-dict frontmatter → `status="illegal"`, `error="non_dict_frontmatter"`
- File read error → `status="illegal"`, `error=<exception_message>`

**Public API**:
```python
def extract_frontmatter(file_path: Path) -> FrontmatterEntry:
    """Extract and validate YAML frontmatter from a Markdown file."""
```

### 3. Concurrent Aggregator (`extractor.py`)

**Purpose**: Process multiple files concurrently and aggregate results.

**Design Pattern** (from `nls.py`):
```python
def _worker_extract(root_str: str, file_str: str) -> FrontmatterEntry:
    """Worker function for ProcessPoolExecutor."""
    # Runs in separate process
    return extract_frontmatter(Path(file_str))
```

**Aggregation Function**:
```python
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
```

**Concurrency Strategy**:
- Use `ProcessPoolExecutor` (not threads) for true parallelism
- `max_workers = min(file_count, n_procs)`
- Collect results via `as_completed()` for progress tracking
- Sort results by file path for deterministic output

### 4. JSON Export (`extractor.py`)

**Purpose**: Write aggregated results to structured JSON file.

```python
def export_json(
    result: AggregatedResult,
    output: Path,
) -> Path:
    """Serialize AggregatedResult to JSON file.
    
    Returns:
        Path to written file.
    """
```

**JSON Format**:
```json
{
  "metadata": {
    "source_directory": "/path/to/scanned",
    "total_files": 150,
    "files_with_frontmatter": 142,
    "files_without_frontmatter": 5,
    "errors": 3,
    "scan_duration_seconds": 2.341,
    "avg_duration_per_file_ms": 15.6
  },
  "files": [
    {
      "file_path": "docs/getting-started.md",
      "frontmatter": {
        "title": "Getting Started",
        "tags": ["tutorial", "beginner"]
      },
      "status": "ok",
      "error": null
    },
    {
      "file_path": "notes/untitled.md",
      "frontmatter": null,
      "status": "illegal",
      "error": "no_frontmatter"
    }
  ]
}
```

---

## CLI Interface

### Command Structure
```
matterify [OPTIONS] COMMAND [ARGS]...
```

### Global Options
| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--debug` | Enable debug logging via structlog |

### `scan` Command
Scan directory and output results to stdout or file.

```
matterify scan DIRECTORY [OPTIONS]
```

| Argument/Option | Description |
|-----------------|-------------|
| `DIRECTORY` | Root directory to scan (required) |
| `-o, --output PATH` | Write JSON to file instead of stdout |
| `--n-procs INT` | Worker process count (default: 4) |
| `-v, --verbose` | Show progress and summary |

**Behavior**:
- Without `--output`: Print JSON to stdout
- With `--output`: Write JSON file, print summary if verbose
- Exit code 0 on success, 1 on error

### `export` Command
Alias for `scan --output` with required output path.

```
matterify export DIRECTORY -o OUTPUT [OPTIONS]
```

| Argument/Option | Description |
|-----------------|-------------|
| `DIRECTORY` | Root directory to scan (required) |
| `-o, --output PATH` | Output JSON file path (required) |
| `--n-procs INT` | Worker process count (default: 4) |
| `-v, --verbose` | Show progress and summary |

---

## Performance Characteristics

### Design Targets
- **Concurrent I/O**: ProcessPoolExecutor for parallel file reading
- **Memory Efficient**: Stream results, don't hold all content in memory
- **Scalable**: Handle 10,000+ files without degradation

### Metrics Logging
When verbose/debug enabled, log:
- Total files scanned
- Runtime duration
- Average time per file
- Files with/without frontmatter
- Error count

---

## Error Handling Strategy

### Graceful Degradation
- Individual file failures do not stop the scan
- Failed files marked with `status="illegal"` and descriptive error
- Summary metadata includes error counts

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, I/O failure) |
| 2 | Configuration error (e.g., invalid n_procs) |

---

## Testing Strategy

### Unit Tests
- `test_models.py`: Dataclass construction and immutability
- `test_scanner.py`: Blacklist filtering, Markdown file discovery
- `test_extractor.py`: Frontmatter parsing, error cases
- `test_aggregator.py`: Concurrent processing, result aggregation

### Integration Tests
- `test_scan_cli.py`: CLI scan command with various options
- `test_export_cli.py`: CLI export command, file output verification

### Test Fixtures
Use `tmp_path` for filesystem operations. Create test directory structures:
```
project/
├── valid.md          # With valid frontmatter
├── no_frontmatter.md # Without frontmatter
├── invalid_yaml.md   # Malformed YAML
└── .git/             # Blacklisted directory
    └── skip.md
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Define data models in `models.py`
2. Implement `iter_markdown_files()` in `scanner.py`
3. Implement `extract_frontmatter()` in `extractor.py`

### Phase 2: Concurrent Processing
1. Implement `_worker_extract()` helper
2. Implement `aggregate_frontmatter()` with ProcessPoolExecutor
3. Add performance timing and metrics

### Phase 3: JSON Export
1. Implement `export_json()` serialization
2. Ensure deterministic output (sorted paths)

### Phase 4: CLI
1. Refactor `cli.py` to use new models and functions
2. Add `scan` and `export` commands with options
3. Integrate verbose output with rich console

### Phase 5: Testing & QA
1. Write unit tests for all components
2. Write integration tests for CLI commands
3. Run ruff, mypy, pytest suite
4. Verify performance with large file sets

---

## Design Decisions Rationale

### Why ProcessPoolExecutor over asyncio?
- YAML parsing is CPU-bound, not I/O-bound
- Avoids GIL contention with true parallelism
- Proven pattern from `nls.py` reference implementation
- Better scalability for large file counts

### Why Frozen Dataclasses?
- Immutability prevents accidental state mutation
- Hashable for use in sets/dicts if needed
- Clear, self-documenting structure
- Type-safe with mypy support

### Why "illegal" Status Pattern?
- Failsafe: bad files don't crash the scan
- Traceable: users can identify problematic files
- Complete output: JSON contains all discovered files
- Consistent with `nls.py` reference design

### Why Blacklist Pruning?
- Avoids scanning irrelevant directories (`.git`, `venv`)
- In-place `dirnames[:]` modification prevents os.walk descent
- Significant performance improvement on large repositories
- Configurable for different project structures
