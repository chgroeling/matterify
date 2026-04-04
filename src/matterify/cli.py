"""CLI entry point for matterify."""

import json as _json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import click
from structlog import get_logger

from matterify import __version__
from matterify.extractor import scan_directory
from matterify.logging import configure_debug_logging, get_console

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
@click.option(
    "--hash/--no-hash",
    "compute_hash",
    default=True,
    help="Disable SHA-256 hash computation.",
)
@click.option(
    "--stats/--no-stats",
    "compute_stats",
    default=True,
    help="Disable file statistics (size, modified time, access time).",
)
@click.option(
    "--frontmatter/--no-frontmatter",
    "compute_frontmatter",
    default=True,
    help="Disable frontmatter extraction.",
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
    compute_hash: bool,
    compute_stats: bool,
    compute_frontmatter: bool,
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
        compute_hash=compute_hash,
        compute_stats=compute_stats,
        compute_frontmatter=compute_frontmatter,
    )

    console: Console = get_console(verbose)

    if verbose:
        console.print(f"Scanning: {directory}")

    from matterify import AggregatedResult

    result: AggregatedResult = scan_directory(
        directory,
        n_procs=n_procs,
        blacklist=exclude,
        compute_hash=compute_hash,
        compute_stats=compute_stats,
        compute_frontmatter=compute_frontmatter,
    )

    result_dict = asdict(result)

    if output:
        output.write_text(_json.dumps(result_dict, indent=2, ensure_ascii=False), encoding="utf-8")
        if verbose:
            console.print(f"Exported to: {output}")
            m = result.metadata
            console.print(f"Total files: {m.total_files}")
            console.print(f"With frontmatter: {m.files_with_frontmatter}")
            console.print(f"Without frontmatter: {m.files_without_frontmatter}")
            console.print(f"Errors: {m.errors}")
            console.print(f"Duration: {m.scan_duration_seconds}s")
    else:
        click.echo(_json.dumps(result_dict, indent=2))
