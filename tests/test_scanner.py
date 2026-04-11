"""Tests for the scanner module."""

from pathlib import Path

from matterify.scanner import DEFAULT_EXCLUDE_PATTERNS, iter_markdown_files


class TestExclude:
    """Tests for default exclude patterns."""

    def test_exclude_is_tuple(self) -> None:
        assert isinstance(DEFAULT_EXCLUDE_PATTERNS, tuple)

    def test_exclude_contains_git(self) -> None:
        assert "**/.git" in DEFAULT_EXCLUDE_PATTERNS

    def test_exclude_contains_node_modules(self) -> None:
        assert "**/node_modules" in DEFAULT_EXCLUDE_PATTERNS

    def test_exclude_contains_venv(self) -> None:
        assert "**/venv" in DEFAULT_EXCLUDE_PATTERNS
        assert "**/.venv" in DEFAULT_EXCLUDE_PATTERNS


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

    def test_prunes_excluded_dirs(self, tmp_path: Path) -> None:
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

    def test_custom_exclude(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom_dir"
        custom.mkdir()
        (custom / "skip.md").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/custom_dir",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_returns_relative_paths(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("# Test", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path))
        assert not files[0].is_absolute()
        assert files[0] == Path("test.md")

    def test_excludes_nested_custom_pattern(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "skip.md").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/sub",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"


class TestGlobPatterns:
    """Tests for glob pattern matching in exclusions."""

    def test_excludes_file_at_root_with_glob_pattern(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# gitignore", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/.gitignore",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_excludes_file_in_nested_directory(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        gitignore = sub / ".gitignore"
        gitignore.write_text("# gitignore", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        (sub / "also_keep.md").write_text("# Also Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/.gitignore",)))
        assert len(files) == 2
        assert all(f.name.endswith(".md") for f in files)

    def test_excludes_file_at_any_depth_with_double_star(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / ".gitignore").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/.gitignore",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_excludes_log_files_with_extension_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "error.log").write_text("Error", encoding="utf-8")
        (tmp_path / "debug.log").write_text("Debug", encoding="utf-8")
        (tmp_path / "readme.md").write_text("# Readme", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/*.log",)))
        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_excludes_markdown_files_with_star_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "skip.markdown").write_text("# Skip", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/*.markdown",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_excludes_multiple_glob_patterns(self, tmp_path: Path) -> None:
        (tmp_path / "a.log").write_text("Log", encoding="utf-8")
        (tmp_path / "b.txt").write_text("Text", encoding="utf-8")
        (tmp_path / "c.md").write_text("# MD", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/*.log", "**/*.txt")))
        assert len(files) == 1
        assert files[0].name == "c.md"

    def test_glob_pattern_matches_nothing_when_no_match(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("# A", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/*.txt",)))
        assert len(files) == 2

    def test_excludes_build_directory_at_any_depth(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        build.mkdir()
        (build / "artifact.md").write_text("# Artifact", encoding="utf-8")
        nested_build = tmp_path / "src" / "build"
        nested_build.mkdir(parents=True)
        (nested_build / "nested_artifact.md").write_text("# Nested", encoding="utf-8")
        (tmp_path / "src" / "main.md").write_text("# Main", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/build",)))
        assert len(files) == 1
        assert files[0].name == "main.md"

    def test_excludes_specific_nested_directory_only(self, tmp_path: Path) -> None:
        left = tmp_path / "left" / "build"
        left.mkdir(parents=True)
        (left / "skip_left.md").write_text("# Skip Left", encoding="utf-8")
        right = tmp_path / "right" / "build"
        right.mkdir(parents=True)
        (right / "skip_right.md").write_text("# Skip Right", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/build",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_excludes_hidden_markdown_files_anywhere(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden.md").write_text("# Hidden", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".also_hidden.md").write_text("# Also Hidden", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/.*.md",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"

    def test_excludes_hidden_file_at_root(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden.md").write_text("# Hidden", encoding="utf-8")
        (tmp_path / "keep.md").write_text("# Keep", encoding="utf-8")
        files = list(iter_markdown_files(tmp_path, exclude=("**/.*",)))
        assert len(files) == 1
        assert files[0].name == "keep.md"
