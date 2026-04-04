"""Tests for the scanner module."""

from pathlib import Path

from matterify.scanner import BLACKLIST, iter_markdown_files


class TestBlacklist:
    """Tests for default blacklist."""

    def test_blacklist_is_tuple(self) -> None:
        assert isinstance(BLACKLIST, tuple)

    def test_blacklist_contains_git(self) -> None:
        assert ".git" in BLACKLIST

    def test_blacklist_contains_node_modules(self) -> None:
        assert "node_modules" in BLACKLIST

    def test_blacklist_contains_venv(self) -> None:
        assert "venv" in BLACKLIST
        assert ".venv" in BLACKLIST


class TestIterMarkdownFiles:
    """Tests for iter_markdown_files."""

    def test_finds_markdown_files(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("# Test", encoding="utf-8")
        (tmp_path / "guide.markdown").write_text("# Guide", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert len(files) == 2
        assert all(f.suffix in {".md", ".markdown"} for f in files)

    def test_excludes_non_markdown(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("# Test", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("Notes", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert len(files) == 1
        assert files[0].name == "test.md"

    def test_recursive_scan(self, tmp_path: Path) -> None:
        sub = tmp_path / "docs"
        sub.mkdir()
        (tmp_path / "readme.md").write_text("# README", encoding="utf-8")
        (sub / "guide.md").write_text("# Guide", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert len(files) == 2

    def test_prunes_blacklisted_dirs(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "skip.md").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_prunes_node_modules(self, tmp_path: Path) -> None:
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "package.md").write_text("# Package", encoding="utf-8")
        (tmp_path / "readme.md").write_text("# README", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_empty_directory(self, tmp_path: Path) -> None:
        files = list(iter_markdown_files(tmp_path))
        assert files == []

    def test_custom_blacklist(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom_dir"
        custom.mkdir()
        (custom / "skip.md").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, blacklist=("custom_dir",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_returns_relative_paths(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("# Test", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert not files[0].is_absolute()
        assert files[0] == Path("test.md")
