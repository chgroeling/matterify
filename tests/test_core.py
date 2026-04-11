"""Tests for the core module."""

from pathlib import Path

from matterify import ScanResults
from matterify.core import _worker_extract, scan_directory
from matterify.enums import FileError, FileStatus
from matterify.models import FileEntry


def _count_lines_callback(content: str) -> object:
    return {"line_count": len(content.splitlines())}


def _return_none_callback(_content: str) -> object | None:
    return None


class TestWorkerExtract:
    """Tests for _worker_extract."""

    def test_worker_returns_complete_entry(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            tmp_path,
            file_path,
            compute_hash=True,
            compute_stats=True,
            compute_frontmatter=True,
        )
        assert isinstance(result, FileEntry)
        assert result.stats is not None
        assert result.stats.file_size is not None
        assert result.stats.modified_time is not None
        assert result.stats.access_time is not None
        assert result.file_hash is not None

    def test_worker_hash_disabled(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            tmp_path,
            file_path,
            compute_hash=False,
            compute_stats=True,
            compute_frontmatter=True,
        )
        assert result.file_hash is None

    def test_worker_stats_disabled(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            tmp_path,
            file_path,
            compute_hash=False,
            compute_stats=False,
            compute_frontmatter=True,
        )
        assert result.stats is None
        assert result.file_hash is None

    def test_worker_frontmatter_disabled(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = _worker_extract(
            tmp_path,
            file_path,
            compute_hash=False,
            compute_stats=False,
            compute_frontmatter=False,
        )
        assert result.status == FileStatus.OK
        assert result.frontmatter is None
        assert result.error is None

    def test_worker_handles_missing_file(self, tmp_path: Path) -> None:
        result = _worker_extract(
            tmp_path,
            tmp_path / "nonexistent.md",
            compute_hash=False,
            compute_stats=False,
            compute_frontmatter=True,
        )
        assert result.status == FileStatus.ILLEGAL
        assert result.error is not None

    def test_worker_callback(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nLine1\nLine2\n", encoding="utf-8")
        result = _worker_extract(
            tmp_path,
            file_path,
            compute_hash=True,
            compute_stats=True,
            compute_frontmatter=True,
            callback=_count_lines_callback,
        )
        assert result.custom_data is not None
        assert result.custom_data["line_count"] == 5


class TestScanDirectory:
    """Tests for scan_directory returning ScanResults."""

    def test_aggregate_collects_all_files(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert result.metadata.total_files == 2
        assert result.metadata.files_with_frontmatter == 2
        assert len(result.files) == 2

    def test_aggregate_metadata_accuracy(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert result.metadata.root == sample_project
        assert result.metadata.errors == 0

    def test_aggregate_file_paths_relative(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        for entry in result.files:
            assert not entry.file_path.is_absolute()

    def test_aggregate_empty_directory(self, tmp_path: Path) -> None:
        result = scan_directory(tmp_path)
        assert result.metadata.total_files == 0
        assert result.files == []

    def test_aggregate_returns_dataclass(self, sample_project: Path) -> None:
        result = scan_directory(sample_project)
        assert isinstance(result, ScanResults)

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
        illegal = [e for e in result.files if e.status == FileStatus.ILLEGAL]
        assert len(illegal) == 1
        assert illegal[0].error == FileError.NON_DICT_FRONTMATTER

    def test_aggregate_respects_blacklist(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()
        (git_dir / "skip.md").write_text("---\ntitle: Skip\n---\nContent", encoding="utf-8")
        (project / "keep.md").write_text("---\ntitle: Keep\n---\nContent", encoding="utf-8")
        result = scan_directory(project)
        assert result.metadata.total_files == 1
        assert result.files[0].file_path == Path("keep.md")

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
        assert result.files[0].file_hash is None

    def test_aggregate_computes_hash_when_enabled(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_hash=True)
        assert result.files[0].stats is not None
        assert result.files[0].file_hash is not None
        assert len(result.files[0].file_hash) == 64

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
        assert result.files[0].stats is None

    def test_aggregate_frontmatter_disabled(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_frontmatter=False)
        assert result.files[0].status == FileStatus.OK
        assert result.files[0].frontmatter is None
        assert result.files[0].error is None
        assert result.metadata.files_with_frontmatter is None
        assert result.metadata.files_without_frontmatter is None

    def test_aggregate_stats_and_frontmatter_disabled(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_stats=False, compute_frontmatter=False)
        assert result.files[0].status == FileStatus.OK
        assert result.files[0].frontmatter is None
        assert result.files[0].error is None
        assert result.files[0].stats is None
        assert result.metadata.files_with_frontmatter is None
        assert result.metadata.files_without_frontmatter is None

    def test_aggregate_includes_non_markdown_file(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.md").write_text("---\ntitle: Main\n---\nContent", encoding="utf-8")
        (project / "extra.txt").write_text("---\ntitle: Extra\n---\nContent", encoding="utf-8")

        result = scan_directory(project, include_files=(Path("extra.txt"),))

        assert result.metadata.total_files == 2
        file_paths = [entry.file_path for entry in result.files]
        assert Path("extra.txt") in file_paths

    def test_aggregate_includes_file_outside_root(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.md").write_text("---\ntitle: Main\n---\nContent", encoding="utf-8")
        external_file = tmp_path / "external.md"
        external_file.write_text("---\ntitle: External\n---\nContent", encoding="utf-8")

        result = scan_directory(project, include_files=(external_file,))

        assert result.metadata.total_files == 2
        file_paths = [entry.file_path for entry in result.files]
        assert external_file.resolve() in file_paths

    def test_aggregate_deduplicates_included_files(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        main_file = project / "main.md"
        main_file.write_text("---\ntitle: Main\n---\nContent", encoding="utf-8")

        result = scan_directory(project, include_files=(main_file, Path("main.md")))

        assert result.metadata.total_files == 1
        assert len(result.files) == 1


class TestCallback:
    """Tests for the callback parameter."""

    def test_callback_receives_content(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nHello\nWorld\n", encoding="utf-8")
        result = scan_directory(project, callback=_count_lines_callback)
        assert result.files[0].custom_data is not None
        assert result.files[0].custom_data["line_count"] == 5

    def test_callback_returns_none(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, callback=_return_none_callback)
        assert result.files[0].custom_data is None

    def test_callback_none_default(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project)
        assert result.files[0].custom_data is None

    def test_callback_with_mixed_files(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "valid.md").write_text("---\ntitle: Valid\n---\nContent", encoding="utf-8")
        (project / "no_fm.md").write_text("# No frontmatter", encoding="utf-8")
        result = scan_directory(project, callback=_count_lines_callback)
        for entry in result.files:
            assert entry.custom_data is not None
            assert "line_count" in entry.custom_data

    def test_callback_without_frontmatter(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "test.md").write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        result = scan_directory(project, compute_frontmatter=False, callback=_count_lines_callback)
        assert result.files[0].status == FileStatus.OK
        assert result.files[0].frontmatter is None
        assert result.files[0].custom_data is not None
        assert result.files[0].custom_data["line_count"] == 4
