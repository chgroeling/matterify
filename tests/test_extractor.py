"""Tests for the extractor module."""

from pathlib import Path

from matterify import AggregatedResult
from matterify.extractor import (
    _extract_frontmatter_from_content,
    _worker_extract,
    scan_directory,
)
from matterify.models import FileEntry


class TestExtractFrontmatterFromContent:
    """Tests for _extract_frontmatter_from_content."""

    def test_extract_valid_frontmatter(
        self,
        sample_md_with_frontmatter: Path,
    ) -> None:
        content = sample_md_with_frontmatter.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(sample_md_with_frontmatter))
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
        content = sample_md_without_frontmatter.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(sample_md_without_frontmatter))
        assert result.status == "illegal"
        assert result.error == "no_frontmatter"
        assert result.frontmatter is None

    def test_extract_invalid_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.md"
        file_path.write_text("---\ninvalid: yaml: broken\n---\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert result.status == "illegal"
        assert result.error == "yaml_parse_error"
        assert result.frontmatter is None

    def test_extract_non_dict_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non_dict.md"
        file_path.write_text("---\n- item1\n- item2\n---\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert result.status == "illegal"
        assert result.error == "non_dict_frontmatter"
        assert result.frontmatter is None

    def test_extract_incomplete_delimiter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "incomplete.md"
        file_path.write_text("---\ntitle: Test\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert result.status == "illegal"
        assert result.error == "no_frontmatter"
        assert result.frontmatter is None

    def test_returns_frontmatter_entry(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert isinstance(result, FileEntry)

    def test_extract_datetime_serialized_to_iso_string(self, tmp_path: Path) -> None:
        file_path = tmp_path / "datetime.md"
        file_path.write_text(
            "---\ntitle: Test\ndate: 2024-03-15\ndatetime: 2024-03-15T10:30:00\n---\nContent",
            encoding="utf-8",
        )
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
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
        result = _extract_frontmatter_from_content(content, str(file_path))
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
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
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
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert result.status == "ok"
        assert result.frontmatter is not None
        assert result.frontmatter["title"] == "Test"
        assert result.frontmatter["tags"] == ["test", "example"]
        assert result.frontmatter["published"] == "2024-03-15"
        assert result.frontmatter["author"] == "John Doe"

    def test_extract_returns_minimal_entry(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert result.stats is None


class TestWorkerExtract:
    """Tests for _worker_extract."""

    def test_worker_returns_complete_entry(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            str(tmp_path), str(file_path), compute_hash=True, compute_stats=True
        )
        assert isinstance(result, FileEntry)
        assert result.stats is not None
        assert result.stats.file_size is not None
        assert result.stats.modified_time is not None
        assert result.stats.access_time is not None
        assert result.stats.file_hash is not None

    def test_worker_hash_disabled(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            str(tmp_path), str(file_path), compute_hash=False, compute_stats=True
        )
        assert result.stats is not None
        assert result.stats.file_hash is None

    def test_worker_stats_disabled(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            str(tmp_path), str(file_path), compute_hash=False, compute_stats=False
        )
        assert result.stats is not None
        assert result.stats.file_size is None
        assert result.stats.modified_time is None
        assert result.stats.access_time is None
        assert result.stats.file_hash is None

    def test_worker_handles_missing_file(self, tmp_path: Path) -> None:
        result = _worker_extract(
            str(tmp_path), str(tmp_path / "nonexistent.md"), compute_hash=False, compute_stats=False
        )
        assert result.status == "illegal"
        assert result.error is not None


class TestScanDirectory:
    """Tests for scan_directory returning AggregatedResult."""

    def test_aggregate_collects_all_files(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert result.metadata.total_files == 2
        assert result.metadata.files_with_frontmatter == 2
        assert len(result.files) == 2

    def test_aggregate_metadata_accuracy(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert result.metadata.source_directory == str(sample_project)
        assert result.metadata.errors == 0

    def test_aggregate_file_paths_relative(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        for entry in result.files:
            assert not entry.file_path.startswith("/")

    def test_aggregate_empty_directory(self, tmp_path: Path) -> None:
        result = scan_directory(tmp_path)
        assert result.metadata.total_files == 0
        assert result.files == []

    def test_aggregate_returns_dataclass(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert isinstance(result, AggregatedResult)

    def test_aggregate_sorted_by_path(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        paths = [e.file_path for e in result.files]
        assert paths == sorted(paths)

    def test_aggregate_with_mixed_files(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "valid.md").write_text("---\ntitle: Valid\n---\nContent", encoding="utf-8")
        (project / "no_fm.md").write_text("# No frontmatter", encoding="utf-8")
        result = scan_directory(project)
        assert result.metadata.total_files == 2
        assert result.metadata.files_with_frontmatter == 1
        assert result.metadata.files_without_frontmatter == 1
        assert result.metadata.errors == 0

    def test_aggregate_with_errors(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "valid.md").write_text("---\ntitle: Valid\n---\nContent", encoding="utf-8")
        (project / "non_dict.md").write_text("---\n- list\n---\nContent", encoding="utf-8")
        result = scan_directory(project)
        assert result.metadata.total_files == 2
        assert result.metadata.files_with_frontmatter == 1
        assert result.metadata.errors == 1
        assert result.metadata.files_without_frontmatter == 0
        illegal = [e for e in result.files if e.status == "illegal"]
        assert len(illegal) == 1
        assert illegal[0].error == "non_dict_frontmatter"

    def test_aggregate_respects_blacklist(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()
        (git_dir / "skip.md").write_text("---\ntitle: Skip\n---\nContent", encoding="utf-8")
        (project / "keep.md").write_text("---\ntitle: Keep\n---\nContent", encoding="utf-8")
        result = scan_directory(project)
        assert result.metadata.total_files == 1
        assert result.files[0].file_path == "keep.md"

    def test_aggregate_timing(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert result.metadata.scan_duration_seconds >= 0
        assert result.metadata.avg_duration_per_file_ms >= 0

    def test_aggregate_file_hash_none_by_default(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_hash=False)
        assert result.files[0].stats is not None
        assert result.files[0].stats.file_size is not None
        assert result.files[0].stats.file_hash is None

    def test_aggregate_computes_hash_when_enabled(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_hash=True)
        assert result.files[0].stats is not None
        assert result.files[0].stats.file_hash is not None
        assert len(result.files[0].stats.file_hash) == 64

    def test_aggregate_file_stats_present(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project)
        assert result.files[0].stats is not None
        assert result.files[0].stats.file_size is not None
        assert result.files[0].stats.modified_time is not None
        assert result.files[0].stats.access_time is not None

    def test_aggregate_file_stats_disabled(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_stats=False)
        assert result.files[0].stats is not None
        assert result.files[0].stats.file_size is None
        assert result.files[0].stats.modified_time is None
        assert result.files[0].stats.access_time is None
