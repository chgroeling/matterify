"""Tests for the export CLI command."""

import json
from pathlib import Path

from click.testing import CliRunner

from matterify.cli import main


def test_export_basic(sample_project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "export.json"
    result = runner.invoke(
        main,
        ["export", str(sample_project), "-o", str(output)],
    )
    assert result.exit_code == 0
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert "files" in data


def test_export_verbose(sample_project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "export.json"
    result = runner.invoke(
        main,
        ["export", str(sample_project), "-o", str(output), "--verbose"],
    )
    assert result.exit_code == 0
    assert "Exported to:" in result.output


def test_export_missing_output_option(sample_project: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["export", str(sample_project)])
    assert result.exit_code != 0


def test_export_nonexistent_directory(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "export.json"
    result = runner.invoke(main, ["export", "/nonexistent/path", "-o", str(output)])
    assert result.exit_code != 0
