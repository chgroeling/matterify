# AGENTS.md

## Project description
`matterify` is a Python utility that recursively scans directory structures for Markdown files, extracts their embedded YAML frontmatter metadata, and aggregates all information into a structured, machine-readable JSON file for further processing.

## Project Structure
```text
matterify/
├── .python-version, pyproject.toml, uv.lock  # Env & Dependency management
├── AGENTS.md, README.md, LICENSE             # Docs & Guidelines
├── src/matterify/                            # Source (src-layout)
│   ├── __init__.py                           # Metadata + public API entry points
│   ├── extractor.py                          # Frontmatter extraction & aggregation logic
│   ├── cli.py                                # Click CLI entry point
│   ├── logging.py                            # Debug & console config
│   └── utils/                                # Utility modules
├── tests/                                    # Pytest suite
│   ├── conftest.py                           # Fixtures
│   ├── test_extractor.py, test_utils.py      # Unit tests
│   └── test_*_cli.py                         # Integration tests
└── docs/                                     # MkDocs source
```

# Development Workflows

### UV Environment & Dependencies
- **Sync:** `uv sync` (add `--all-extras` for dev/docs).
- **Update:** `uv lock --upgrade`.
- **Management:** `uv add <pkg>` (use `--dev` for dev); `uv remove <pkg>`; `uv pip list`.
- **Strategy:** Use min constraints (e.g., `click>=8.1.0`) in `pyproject.toml`; rely on `uv.lock` for reproducibility. Avoid manual lock edits.

### Execution & Lifecycle
- **Run:** `uv run [matterify|python script.py|tool] [args]`.
- **Project:** `uv init` (setup); `uv check` (compat-check).
- **Dist:** `uv build` (wheel/sdist); `uv publish` (upload).

### Standards & Git
- **Versioning:** Strict SemVer (`MAJOR.MINOR.PATCH`).
- **Commits:** Follow Conventional Commits (e.g., `feat:`, `fix:`, `chore:`).
- **Automation:** **Never** commit autonomously; only execute on explicit user request.

## Testing & QA

### Quality Checks
**Tools:** `ruff` (lint/fmt), `mypy` (types). Prefix cmds with `uv run`.
- **Fmt/Lint:** `ruff format [--check] src/ tests/`, `ruff check src/ tests/`
- **Types:** `mypy src/`
- **Pre-Commit Gate:** `uv run ruff format src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest`

### Tests (`uv run pytest`)
- **Exec:** `.` (all), `-v` (verbose), `tests/[file].py[::func]` (targeted), `--cov=matterify --cov-report=html` (coverage).
- **Structure:** `tests/` dir 1:1 mapping (`extractor.py`->`test_extractor.py`, `utils/__init__.py`->`test_utils.py`). `cli.py` splits to `test_cli.py` (smoke), `test_[scan|export]_cli.py`.
- **FS Rules:** Prioritize critical paths. Use `tmp_path`. Name staging dirs `project/` (avoids `src/src/` nesting).
- **Paths:** Stored paths include top-level prefix (`project/src/main.py`). Assert via `endswith()` or `rglob()`.
- **Public API only:** Never import or call private symbols (names starting with `_`) from `src/` in tests. Test behaviour exclusively through the public API.
- **No inline imports:** All imports must be at the top of the test file. `import` statements inside test functions are forbidden.

## Tech Stack & Standards
- **Runtime:** Python 3.12.3
- **Concurrency:** `asyncio` (core)
- **Package Mgmt:** `uv` via `pyproject.toml` (Build: `hatchling`)
- **CLI/UI:** `click` (commands); `rich` (UI/verbose)
- **Logging:** `structlog` (debug/structured)
- **Parsing:** `pyyaml` (YAML Frontmatter)
- **Quality:** `ruff` (lint/fmt); `mypy` (strict)
- **Testing:** `pytest` (plugins: `benchmark`, `asyncio`)
- **Docs:** `mkdocs` with Material theme

## Coding Standards
- **Typing:** Strict `mypy` for `src/`; relaxed for `tests/`.
- **Type Aliases:** Use PEP 695 `type X = ...` (Python 3.12+). **Avoid** `TypeAlias` (ruff `UP040`).
- **Format:** PEP8 via `ruff`; 100 char limit.
- **Testing:** ≥1 unit test/function; use `tmp_path` for FS.
- **UI/Logging:** CLI silent by default. Use `structlog` for internal debug logs and `rich` for verbose user feedback. **Strictly isolate** UI output from internal loggers.

### Import Rules (ruff)
- **Order (I001):** stdlib → third-party → local. Separate with one blank line. Run `uv run ruff check --fix` or `format` to resolve.
- **Unused Imports (F401):** Remove immediately; every import must be referenced.
- **`TYPE_CHECKING` (TC005):** Delete empty `if TYPE_CHECKING: pass` blocks; use only if containing symbols.
- **Async-safe I/O (ASYNC240):** Never call blocking `pathlib.Path` methods inside `async def`. Wrap with `asyncio.to_thread(path.method, ...)`.
- **Pathlib over `os` (PTH):** Use `pathlib` equivalents (e.g., `Path.unlink()`) over `os`. Avoid `os` unless no `pathlib` alternative exists.
- **`contextlib.suppress` (SIM105):** Replace `try: ... except Error: pass` with `with contextlib.suppress(Error):`.

### mypy Rules (strict)
- **Return types:** All functions (including `__exit__`) require explicit annotations.
- **`__exit__` signature:** Use exact typing:
  ```python
  def __exit__(
      self,
      exc_type: type[BaseException] | None,
      exc_val: BaseException | None,
      exc_tb: TracebackType | None,
  ) -> None:
  ```
  Import `TracebackType` from `types` (use `if TYPE_CHECKING:` if preferred).
- **`asyncio.to_thread`:** Pass bound methods directly: `asyncio.to_thread(path.read_text, encoding="utf-8")`. Avoid lambdas to preserve return-type inference.

## Python API
<!-- To be defined as the project evolves -->

## CLI
<!-- To be defined as the project evolves -->

## Logging & UI (`src/matterify/logging.py`)
- `configure_debug_logging(enabled)`: Configures `structlog`. Use `logging.CRITICAL` (50) for no-op. **Avoid `logging.CRITICAL + 1`** (causes `KeyError`).
- `get_console(verbose)`: Returns `rich.Console()`. Verbose writes to **stdout** for `CliRunner` capture; otherwise `quiet=True`.

### structlog Rules
- **Init**: Use `structlog.get_logger(__name__)`. **Never** `logging.getLogger()`.
- **Context**: Use kwargs: `logger.debug("msg", k=v)`. **Never** `extra={...}` (crashes on reserved keys like `name`).

### Established log fields
<!-- To be defined as the project evolves -->

## Architecture & Mechanisms
<!-- To be defined as the project evolves -->

## Docstring Rules
- **Format:** Google Style (`Args:`, `Returns:`, `Raises:`).
- **Markup:** Markdown ONLY; NO reST/Sphinx directives (`:class:`, etc.).
- **Code/Links:** Backticks (single inline, triple block). MkDocs autorefs (`[MyClass][]`).
- **Types:** Rely on Python type hints; do not duplicate in docstrings.
- **Style:** PEP 257 imperative mood ("Return X", not "Returns X").
- **Length:** One-liners for simple/private. Multi-line/sections ONLY for complex/public APIs. Omit redundant `Args:`/`Returns:`.
- **Staleness:** Always update docstrings, inline comments, and class `Supported modes:` when implementing scaffolds. Treat stale "not yet implemented" text as a bug.
