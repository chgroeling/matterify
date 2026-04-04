"""CLI entry point for matterify."""

from pathlib import Path
from typing import TYPE_CHECKING

import click

from matterify import __version__
from matterify.extractor import aggregate_frontmatter, export_json
from matterify.logging import configure_debug_logging, get_console

if TYPE_CHECKING:
    from rich.console import Console


@click.group()
@click.version_option(version=__version__, prog_name="matterify")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.pass_context
def main(ctx: click.Context, debug: bool) -> None:
    """Matterify - Extract YAML frontmatter from Markdown files."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    configure_debug_logging(debug)


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output JSON file path.",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output.")
@click.pass_context
def scan(ctx: click.Context, directory: Path, output: Path | None, verbose: bool) -> None:
    """Scan a directory for Markdown files and extract frontmatter."""
    console: Console = get_console(verbose)

    if verbose:
        console.print(f"Scanning: {directory}")

    import asyncio
    import json as _json

    if output:
        result_path = asyncio.run(export_json(directory, output))
        if verbose:
            console.print(f"Exported to: {result_path}")
    else:
        result = asyncio.run(aggregate_frontmatter(directory))
        click.echo(_json.dumps(result, indent=2))


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output JSON file path.",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output.")
@click.pass_context
def export(ctx: click.Context, directory: Path, output: Path, verbose: bool) -> None:
    """Export aggregated frontmatter to a JSON file."""
    console: Console = get_console(verbose)

    import asyncio

    result_path = asyncio.run(export_json(directory, output))

    if verbose:
        console.print(f"Exported to: {result_path}")
