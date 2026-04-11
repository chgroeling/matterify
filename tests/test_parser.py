"""Tests for the parser module."""

from pathlib import Path

from matterify.enums import FileError, FileStatus
from matterify.parser import _extract_frontmatter_from_content


class TestExtractFrontmatterFromContent:
    """Tests for _extract_frontmatter_from_content."""

    def test_extract_valid_frontmatter(
        self,
        sample_md_with_frontmatter: Path,
    ) -> None:
        content = sample_md_with_frontmatter.read_text(encoding="utf-8")
        _, frontmatter, status, error = _extract_frontmatter_from_content(
            content, str(sample_md_with_frontmatter)
        )
        assert status == FileStatus.OK
        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "Test Author"
        assert frontmatter["tags"] == ["test", "example"]
        assert error is None

    def test_extract_no_frontmatter(
        self,
        sample_md_without_frontmatter: Path,
    ) -> None:
        content = sample_md_without_frontmatter.read_text(encoding="utf-8")
        _, frontmatter, status, error = _extract_frontmatter_from_content(
            content, str(sample_md_without_frontmatter)
        )
        assert status == FileStatus.ILLEGAL
        assert error == FileError.NO_FRONTMATTER
        assert frontmatter is None

    def test_extract_invalid_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.md"
        file_path.write_text("---\ninvalid: yaml: broken\n---\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        _, frontmatter, status, error = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.ILLEGAL
        assert error == FileError.YAML_PARSE_ERROR
        assert frontmatter is None

    def test_extract_non_dict_frontmatter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "non_dict.md"
        file_path.write_text("---\n- item1\n- item2\n---\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        _, frontmatter, status, error = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.ILLEGAL
        assert error == FileError.NON_DICT_FRONTMATTER
        assert frontmatter is None

    def test_extract_incomplete_delimiter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "incomplete.md"
        file_path.write_text("---\ntitle: Test\n", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        _, frontmatter, status, error = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.ILLEGAL
        assert error == FileError.NO_FRONTMATTER
        assert frontmatter is None

    def test_returns_tuple(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_extract_datetime_serialized_to_iso_string(self, tmp_path: Path) -> None:
        file_path = tmp_path / "datetime.md"
        file_path.write_text(
            "---\ntitle: Test\ndate: 2024-03-15\ndatetime: 2024-03-15T10:30:00\n---\nContent",
            encoding="utf-8",
        )
        content = file_path.read_text(encoding="utf-8")
        _, frontmatter, status, _ = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.OK
        assert frontmatter is not None
        assert frontmatter["date"] == "2024-03-15"
        assert frontmatter["datetime"] == "2024-03-15T10:30:00"

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
        _, frontmatter, status, _ = result
        assert status == FileStatus.OK
        assert frontmatter is not None
        assert frontmatter["metadata"]["created"] == "2024-01-01"
        assert frontmatter["metadata"]["updated"] == "2024-06-15T14:00:00"

    def test_extract_list_with_datetime_serialized(self, tmp_path: Path) -> None:
        file_path = tmp_path / "list.md"
        file_path.write_text(
            "---\ntitle: Test\nevents:\n  - 2024-01-01\n  - 2024-02-15\n---\nContent",
            encoding="utf-8",
        )
        content = file_path.read_text(encoding="utf-8")
        _, frontmatter, status, _ = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.OK
        assert frontmatter is not None
        assert frontmatter["events"] == ["2024-01-01", "2024-02-15"]

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
        _, frontmatter, status, _ = _extract_frontmatter_from_content(content, str(file_path))
        assert status == FileStatus.OK
        assert frontmatter is not None
        assert frontmatter["title"] == "Test"
        assert frontmatter["tags"] == ["test", "example"]
        assert frontmatter["published"] == "2024-03-15"
        assert frontmatter["author"] == "John Doe"

    def test_extract_returns_tuple_elements(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
        content = file_path.read_text(encoding="utf-8")
        result = _extract_frontmatter_from_content(content, str(file_path))
        assert isinstance(result[0], str)
        assert isinstance(result[1], dict | None)
        assert isinstance(result[2], FileStatus)
        assert result[3] is None or isinstance(result[3], FileError)
