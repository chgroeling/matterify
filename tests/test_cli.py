"""Smoke tests for the CLI."""

from click.testing import CliRunner

from matterify.cli import main


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "matterify" in result.output


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Extract YAML frontmatter" in result.output
