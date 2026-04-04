"""CLI entry point for matterify."""

import json as _json
from pathlib import Path
from typing import TYPE_CHECKING

import click
from structlog import get_logger

from matterify import __version__
from matterify.extractor import _aggregate_dataclass, export_json
from matterify.logging import configure_debug_logging, get_console
from matterify.scanner import BLACKLIST

if TYPE_CHECKING:
    from rich.console import Console

logger = get_logger(__name__)


@click.command()
@click.version_option(version=__version__, prog_name="matterify")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write JSON to file instead of stdout.",
)
@click.option(
    "--n-procs",
    type=int,
    default=None,
    help="Worker process count (default: auto-detect CPU cores).",
)
@click.option("--verbose", "-v", is_flag=True, help="Show progress and summary.")
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Directories to exclude from scanning.",
)
@click.pass_context
def main(
    ctx: click.Context,
    directory: Path,
    debug: bool,
    output: Path | None,
    n_procs: int | None,
    verbose: bool,
    exclude: tuple[str, ...],
) -> None:
    """Matterify - Extract YAML frontmatter from Markdown files."""
    ctx.ensure_object(dict)
    configure_debug_logging(debug)

    logger.debug(
        "cli_invoked",
        directory=str(directory),
        debug=debug,
        output=str(output) if output else None,
        n_procs=n_procs,
        verbose=verbose,
        exclude=list(exclude) if exclude else [],
    )

    console: Console = get_console(verbose)
    blacklist = exclude if exclude else BLACKLIST

    if verbose:
        console.print(f"Scanning: {directory}")

    result = _aggregate_dataclass(directory, n_procs=n_procs, blacklist=blacklist)

    if output:
        result_path = export_json(result, output)
        if verbose:
            console.print(f"Exported to: {result_path}")
            m = result.metadata
            console.print(f"Total files: {m.total_files}")
            console.print(f"With frontmatter: {m.files_with_frontmatter}")
            console.print(f"Without frontmatter: {m.files_without_frontmatter}")
            console.print(f"Errors: {m.errors}")
            console.print(f"Duration: {m.scan_duration_seconds}s")
    else:
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
        click.echo(_json.dumps(data, indent=2))
