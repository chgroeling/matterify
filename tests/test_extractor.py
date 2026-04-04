"""Tests for the extractor module."""

import json
from pathlib import Path

from matterify.extractor import (
    aggregate_frontmatter,
    export_json,
    extract_frontmatter,
    scan_markdown_files,
)


class TestExtractFrontmatter:
    """Tests for extract_frontmatter."""

    async def test_extract_valid_frontmatter(
        self,
        sample_md_with_frontmatter: Path,
    ) -> None:
        result = await extract_frontmatter(sample_md_with_frontmatter)
        assert result is not None
        assert result["title"] == "Test Document"
        assert result["author"] == "Test Author"
        assert result["tags"] == ["test", "example"]

    async def test_extract_no_frontmatter(
        self,
        sample_md_without_frontmatter: Path,
    ) -> None:
        result = await extract_frontmatter(sample_md_without_frontmatter)
        assert result is None

    async def test_extract_invalid_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.md"
        file_path.write_text("---\ninvalid: yaml: broken\n---\n", encoding="utf-8")
        result = await extract_frontmatter(file_path)
        assert result is None

    async def test_extract_non_dict_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non_dict.md"
        file_path.write_text("---\n- item1\n- item2\n---\n", encoding="utf-8")
        result = await extract_frontmatter(file_path)
        assert result is None

    async def test_extract_incomplete_delimiter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "incomplete.md"
        file_path.write_text("---\ntitle: Test\n", encoding="utf-8")
        result = await extract_frontmatter(file_path)
        assert result is None


class TestScanMarkdownFiles:
    """Tests for scan_markdown_files."""

    async def test_scan_finds_markdown_files(self, sample_project: Path) -> None:
        files = await scan_markdown_files(sample_project)
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    async def test_scan_excludes_non_markdown(self, sample_project: Path) -> None:
        files = await scan_markdown_files(sample_project)
        assert not any(f.suffix == ".txt" for f in files)

    async def test_scan_recursive(self, sample_project: Path) -> None:
        files = await scan_markdown_files(sample_project)
        paths = [f.name for f in files]
        assert "readme.md" in paths
        assert "guide.md" in paths

    async def test_scan_empty_directory(self, tmp_path: Path) -> None:
        files = await scan_markdown_files(tmp_path)
        assert files == []

    async def test_scan_sorted_results(self, sample_project: Path) -> None:
        files = await scan_markdown_files(sample_project)
        assert files == sorted(files)


class TestAggregateFrontmatter:
    """Tests for aggregate_frontmatter."""

    async def test_aggregate_collects_all_files(self, sample_project: Path) -> None:
        result = await aggregate_frontmatter(sample_project)
        assert result["metadata"]["total_files"] == 2
        assert result["metadata"]["files_with_frontmatter"] == 2
        assert len(result["files"]) == 2

    async def test_aggregate_metadata_accuracy(self, sample_project: Path) -> None:
        result = await aggregate_frontmatter(sample_project)
        assert result["metadata"]["source_directory"] == str(sample_project)
        assert result["metadata"]["errors"] == 0

    async def test_aggregate_file_paths_relative(self, sample_project: Path) -> None:
        result = await aggregate_frontmatter(sample_project)
        for entry in result["files"]:
            assert not entry["file"].startswith("/")

    async def test_aggregate_empty_directory(self, tmp_path: Path) -> None:
        result = await aggregate_frontmatter(tmp_path)
        assert result["metadata"]["total_files"] == 0
        assert result["files"] == []


class TestExportJson:
    """Tests for export_json."""

    async def test_export_creates_json_file(self, sample_project: Path, tmp_path: Path) -> None:
        output = tmp_path / "output.json"
        result_path = await export_json(sample_project, output)
        assert result_path == output
        assert output.exists()

    async def test_export_valid_json(self, sample_project: Path, tmp_path: Path) -> None:
        output = tmp_path / "output.json"
        await export_json(sample_project, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        assert "metadata" in data
        assert "files" in data

    async def test_export_content_matches_aggregate(
        self,
        sample_project: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "output.json"
        await export_json(sample_project, output)
        content = output.read_text(encoding="utf-8")
        exported = json.loads(content)
        aggregated = await aggregate_frontmatter(sample_project)
        assert exported["metadata"] == aggregated["metadata"]
