"""Tests for the CLI."""

import json
from pathlib import Path

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


def test_scan_basic(sample_project: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [str(sample_project)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["metadata"]["total_files"] == 2
    assert "stats" in data["files"][0]
    assert "file_size" not in data["files"][0]


def test_scan_verbose(sample_project: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, [str(sample_project), "--verbose"])
    assert result.exit_code == 0
    assert "Scanning:" in result.output


def test_scan_with_output(sample_project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "scan_output.json"
    result = runner.invoke(main, [str(sample_project), "-o", str(output)])
    assert result.exit_code == 0
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["metadata"]["total_files"] == 2
    assert "stats" in data["files"][0]
    assert "file_size" not in data["files"][0]


def test_scan_verbose_with_output(sample_project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "scan_output.json"
    result = runner.invoke(
        main,
        [str(sample_project), "-o", str(output), "--verbose"],
    )
    assert result.exit_code == 0
    assert "Exported to:" in result.output


def test_scan_nonexistent_directory() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["/nonexistent/path"])
    assert result.exit_code != 0
