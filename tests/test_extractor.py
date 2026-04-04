"""Tests for the extractor module."""

import json
from pathlib import Path

from matterify.extractor import (
    _aggregate_dataclass,
    aggregate_frontmatter,
    export_json,
    extract_frontmatter,
)
from matterify.models import FrontmatterEntry


class TestExtractFrontmatter:
    """Tests for extract_frontmatter."""

    def test_extract_valid_frontmatter(
        self,
        sample_md_with_frontmatter: Path,
    ) -> None:
        result = extract_frontmatter(sample_md_with_frontmatter)
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["title"] == "Test Document"
        assert result.frontmatter["author"] == "Test Author"
        assert result.frontmatter["tags"] == ["test", "example"]
        assert result.error is None

    def test_extract_no_frontmatter(
        self,
        sample_md_without_frontmatter: Path,
    ) -> None:
        result = extract_frontmatter(sample_md_without_frontmatter)
        assert result.status == "illegal"
        assert result.error == "no_frontmatter"
        assert result.frontmatter is None

    def test_extract_invalid_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.md"
        file_path.write_text("---\ninvalid: yaml: broken\n---\n", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.status == "illegal"
        assert result.error == "yaml_parse_error"
        assert result.frontmatter is None

    def test_extract_non_dict_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non_dict.md"
        file_path.write_text("---\n- item1\n- item2\n---\n", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.status == "illegal"
        assert result.error == "non_dict_frontmatter"
        assert result.frontmatter is None

    def test_extract_incomplete_delimiter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "incomplete.md"
        file_path.write_text("---\ntitle: Test\n", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.status == "illegal"
        assert result.error == "no_frontmatter"
        assert result.frontmatter is None

    def test_returns_frontmatter_entry(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert isinstance(result, FrontmatterEntry)

    def test_extract_datetime_serialized_to_iso_string(self, tmp_path: Path) -> None:
        file_path = tmp_path / "datetime.md"
        file_path.write_text(
            "---\ntitle: Test\ndate: 2024-03-15\ndatetime: 2024-03-15T10:30:00\n---\nContent",
            encoding="utf-8",
        )
        result = extract_frontmatter(file_path)
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["date"] == "2024-03-15"
        assert result.frontmatter["datetime"] == "2024-03-15T10:30:00"

    def test_extract_nested_datetime_serialized(self, tmp_path: Path) -> None:
        file_path = tmp_path / "nested.md"
        content = (
            "---\n"
            "title: Test\n"
            "metadata:\n"
            "  created: 2024-01-01\n"
            "  updated: 2024-06-15T14:00:00\n"
            "---\n"
            "Content"
        )
        file_path.write_text(content, encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["metadata"]["created"] == "2024-01-01"
        assert result.frontmatter["metadata"]["updated"] == "2024-06-15T14:00:00"

    def test_extract_list_with_datetime_serialized(self, tmp_path: Path) -> None:
        file_path = tmp_path / "list.md"
        file_path.write_text(
            "---\ntitle: Test\nevents:\n  - 2024-01-01\n  - 2024-02-15\n---\nContent",
            encoding="utf-8",
        )
        result = extract_frontmatter(file_path)
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["events"] == ["2024-01-01", "2024-02-15"]

    def test_extract_mixed_content_with_datetime(self, tmp_path: Path) -> None:
        file_path = tmp_path / "mixed.md"
        content = (
            "---\n"
            "title: Test\n"
            "tags:\n"
            "  - test\n"
            "  - example\n"
            "published: 2024-03-15\n"
            "author: John Doe\n"
            "---\n"
            "Content"
        )
        file_path.write_text(content, encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["title"] == "Test"
        assert result.frontmatter["tags"] == ["test", "example"]
        assert result.frontmatter["published"] == "2024-03-15"
        assert result.frontmatter["author"] == "John Doe"

    def test_extract_includes_file_size(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.file_size is not None
        assert result.file_size > 0

    def test_extract_includes_modified_time(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.modified_time is not None

    def test_extract_includes_access_time(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = extract_frontmatter(file_path)
        assert result.access_time is not None


class TestAggregateFrontmatter:
    """Tests for aggregate_frontmatter returning dict."""

    def test_aggregate_collects_all_files(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        assert result["metadata"]["total_files"] == 2
        assert result["metadata"]["files_with_frontmatter"] == 2
        assert len(result["files"]) == 2

    def test_aggregate_metadata_accuracy(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        assert result["metadata"]["source_directory"] == str(sample_project)
        assert result["metadata"]["errors"] == 0

    def test_aggregate_file_paths_relative(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        for entry in result["files"]:
            assert not entry["file_path"].startswith("/")

    def test_aggregate_empty_directory(self, tmp_path: Path) -> None:
        result = aggregate_frontmatter(tmp_path)
        assert result["metadata"]["total_files"] == 0
        assert result["files"] == []

    def test_aggregate_returns_dict(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        assert isinstance(result, dict)

    def test_aggregate_sorted_by_path(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        paths = [e["file_path"] for e in result["files"]]
        assert paths == sorted(paths)

    def test_aggregate_with_mixed_files(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "valid.md").write_text("---\ntitle: Valid\n---\nContent", encoding="utf-8")
        (project / "no_fm.md").write_text("# No frontmatter", encoding="utf-8")
        result = aggregate_frontmatter(project)
        assert result["metadata"]["total_files"] == 2
        assert result["metadata"]["files_with_frontmatter"] == 1
        assert result["metadata"]["files_without_frontmatter"] == 1
        assert result["metadata"]["errors"] == 0

    def test_aggregate_with_errors(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "valid.md").write_text("---\ntitle: Valid\n---\nContent", encoding="utf-8")
        (project / "non_dict.md").write_text("---\n- list\n---\nContent", encoding="utf-8")
        result = aggregate_frontmatter(project)
        assert result["metadata"]["total_files"] == 2
        assert result["metadata"]["files_with_frontmatter"] == 1
        assert result["metadata"]["errors"] == 1
        assert result["metadata"]["files_without_frontmatter"] == 0
        illegal = [e for e in result["files"] if e["status"] == "illegal"]
        assert len(illegal) == 1
        assert illegal[0]["error"] == "non_dict_frontmatter"

    def test_aggregate_respects_blacklist(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()
        (git_dir / "skip.md").write_text("---\ntitle: Skip\n---\nContent", encoding="utf-8")
        (project / "keep.md").write_text("---\ntitle: Keep\n---\nContent", encoding="utf-8")
        result = aggregate_frontmatter(project)
        assert result["metadata"]["total_files"] == 1
        assert result["files"][0]["file_path"] == "keep.md"

    def test_aggregate_timing(self, sample_project: Path) -> None:
        result = aggregate_frontmatter(sample_project)
        assert result["metadata"]["scan_duration_seconds"] >= 0
        assert result["metadata"]["avg_duration_per_file_ms"] >= 0


class TestExportJson:
    """Tests for export_json."""

    def test_export_creates_json_file(self, sample_project: Path, tmp_path: Path) -> None:
        result = _aggregate_dataclass(sample_project)
        output = tmp_path / "output.json"
        result_path = export_json(result, output)
        assert result_path == output
        assert output.exists()

    def test_export_valid_json(self, sample_project: Path, tmp_path: Path) -> None:
        result = _aggregate_dataclass(sample_project)
        output = tmp_path / "output.json"
        export_json(result, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        assert "metadata" in data
        assert "files" in data

    def test_export_metadata_fields(self, sample_project: Path, tmp_path: Path) -> None:
        result = _aggregate_dataclass(sample_project)
        output = tmp_path / "output.json"
        export_json(result, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        meta = data["metadata"]
        assert "source_directory" in meta
        assert "total_files" in meta
        assert "files_with_frontmatter" in meta
        assert "files_without_frontmatter" in meta
        assert "errors" in meta
        assert "scan_duration_seconds" in meta
        assert "avg_duration_per_file_ms" in meta

    def test_export_file_entry_fields(self, sample_project: Path, tmp_path: Path) -> None:
        result = _aggregate_dataclass(sample_project)
        output = tmp_path / "output.json"
        export_json(result, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        assert len(data["files"]) == 2
        for entry in data["files"]:
            assert "file_path" in entry
            assert "frontmatter" in entry
            assert "status" in entry
            assert "error" in entry
            assert "file_size" in entry
            assert "modified_time" in entry
            assert "access_time" in entry

    def test_export_content_matches_aggregate(
        self,
        sample_project: Path,
        tmp_path: Path,
    ) -> None:
        result = _aggregate_dataclass(sample_project)
        output = tmp_path / "output.json"
        export_json(result, output)
        content = output.read_text(encoding="utf-8")
        exported = json.loads(content)
        assert exported["metadata"]["total_files"] == result.metadata.total_files
        assert (
            exported["metadata"]["files_with_frontmatter"] == result.metadata.files_with_frontmatter
        )

    def test_export_json_with_datetime_serialized(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "doc.md").write_text(
            "---\ntitle: Doc\ndate: 2024-03-15\ndatetime: 2024-03-15T10:30:00\n---\nContent",
            encoding="utf-8",
        )
        result = _aggregate_dataclass(project)
        output = tmp_path / "output.json"
        export_json(result, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["files"][0]["frontmatter"]["date"] == "2024-03-15"
        assert data["files"][0]["frontmatter"]["datetime"] == "2024-03-15T10:30:00"
