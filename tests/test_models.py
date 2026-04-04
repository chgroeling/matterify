"""Tests for the models module."""

from matterify.models import AggregatedResult, FrontmatterEntry, ScanMetadata


class TestFrontmatterEntry:
    """Tests for FrontmatterEntry dataclass."""

    def test_create_ok_entry(self) -> None:
        entry = FrontmatterEntry(
            file_path="docs/test.md",
            frontmatter={"title": "Test"},
            status="ok",
            error=None,
        )
        assert entry.file_path == "docs/test.md"
        assert entry.frontmatter == {"title": "Test"}
        assert entry.status == "ok"
        assert entry.error is None

    def test_create_illegal_entry(self) -> None:
        entry = FrontmatterEntry(
            file_path="notes/bad.md",
            frontmatter=None,
            status="illegal",
            error="no_frontmatter",
        )
        assert entry.file_path == "notes/bad.md"
        assert entry.frontmatter is None
        assert entry.status == "illegal"
        assert entry.error == "no_frontmatter"

    def test_immutability(self) -> None:
        entry = FrontmatterEntry(
            file_path="test.md",
            frontmatter={"title": "Test"},
            status="ok",
            error=None,
        )
        try:
            entry.status = "illegal"
            raise AssertionError("Should not be able to modify frozen dataclass")
        except AttributeError:
            pass

    def test_not_hashable_with_dict(self) -> None:
        entry = FrontmatterEntry(
            file_path="test.md",
            frontmatter={"title": "Test"},
            status="ok",
            error=None,
        )
        try:
            hash(entry)
            raise AssertionError("Should not be hashable with dict frontmatter")
        except TypeError:
            pass

    def test_hashable_with_none_frontmatter(self) -> None:
        entry = FrontmatterEntry(
            file_path="test.md",
            frontmatter=None,
            status="illegal",
            error="no_frontmatter",
        )
        entry_set = {entry}
        assert entry in entry_set


class TestScanMetadata:
    """Tests for ScanMetadata dataclass."""

    def test_create_metadata(self) -> None:
        metadata = ScanMetadata(
            source_directory="/path/to/dir",
            total_files=10,
            files_with_frontmatter=8,
            files_without_frontmatter=1,
            errors=1,
            scan_duration_seconds=1.5,
            avg_duration_per_file_ms=150.0,
            throughput_files_per_second=6.7,
        )
        assert metadata.source_directory == "/path/to/dir"
        assert metadata.total_files == 10
        assert metadata.files_with_frontmatter == 8
        assert metadata.files_without_frontmatter == 1
        assert metadata.errors == 1
        assert metadata.scan_duration_seconds == 1.5
        assert metadata.avg_duration_per_file_ms == 150.0
        assert metadata.throughput_files_per_second == 6.7

    def test_immutability(self) -> None:
        metadata = ScanMetadata(
            source_directory="/path",
            total_files=0,
            files_with_frontmatter=0,
            files_without_frontmatter=0,
            errors=0,
            scan_duration_seconds=0.0,
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        )
        try:
            metadata.total_files = 1
            raise AssertionError("Should not be able to modify frozen dataclass")
        except AttributeError:
            pass


class TestAggregatedResult:
    """Tests for AggregatedResult dataclass."""

    def test_create_result(self) -> None:
        metadata = ScanMetadata(
            source_directory="/path",
            total_files=1,
            files_with_frontmatter=1,
            files_without_frontmatter=0,
            errors=0,
            scan_duration_seconds=0.1,
            avg_duration_per_file_ms=100.0,
            throughput_files_per_second=10.0,
        )
        entry = FrontmatterEntry(
            file_path="test.md",
            frontmatter={"title": "Test"},
            status="ok",
            error=None,
        )
        result = AggregatedResult(metadata=metadata, files=[entry])
        assert result.metadata.total_files == 1
        assert len(result.files) == 1
        assert result.files[0].status == "ok"

    def test_aggregated_result_immutability(self) -> None:
        metadata = ScanMetadata(
            source_directory="/path",
            total_files=0,
            files_with_frontmatter=0,
            files_without_frontmatter=0,
            errors=0,
            scan_duration_seconds=0.0,
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        )
        result = AggregatedResult(metadata=metadata, files=[])
        try:
            result.files = []
            raise AssertionError("Should not be able to modify frozen dataclass")
        except AttributeError:
            pass
