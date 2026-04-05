"""Tests for the cache module and cache-backed scan behavior."""

from pathlib import Path

import pytest

from matterify.cache import (
    build_scan_cache_key,
    clear_cache,
    get_cached_scan_result,
    set_cached_scan_result,
)
from matterify.extractor import scan_directory
from matterify.models import AggregatedResult, ScanMetadata


@pytest.fixture(autouse=True)
def clear_single_entry_cache() -> None:
    """Clear cache before and after each test for isolation."""
    clear_cache()
    yield
    clear_cache()


def _make_result(source_directory: str = "project") -> AggregatedResult:
    """Create an AggregatedResult for cache unit tests."""
    metadata = ScanMetadata(
        source_directory=source_directory,
        total_files=1,
        files_with_frontmatter=1,
        files_without_frontmatter=0,
        errors=0,
        scan_duration_seconds=0.1,
        avg_duration_per_file_ms=100.0,
        throughput_files_per_second=10.0,
    )

    return AggregatedResult(metadata=metadata, files=[])


def test_build_scan_cache_key_normalizes_directory_and_blacklist(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    key = build_scan_cache_key(
        directory=project,
        effective_n_procs=4,
        effective_blacklist=("b", "a"),
        compute_hash=True,
        compute_stats=False,
        compute_frontmatter=True,
    )

    assert key[0] == str(project.resolve())
    assert key[2] == ("a", "b")


def test_set_and_get_cached_scan_result_round_trip(tmp_path: Path) -> None:
    key = build_scan_cache_key(
        directory=tmp_path,
        effective_n_procs=2,
        effective_blacklist=(".git",),
        compute_hash=True,
        compute_stats=True,
        compute_frontmatter=True,
    )
    result = _make_result(source_directory=str(tmp_path))

    set_cached_scan_result(key, result)
    cached = get_cached_scan_result(key)

    assert cached is result


def test_get_cached_scan_result_returns_none_for_non_matching_key(tmp_path: Path) -> None:
    first_key = build_scan_cache_key(
        directory=tmp_path / "one",
        effective_n_procs=2,
        effective_blacklist=(".git",),
        compute_hash=True,
        compute_stats=True,
        compute_frontmatter=True,
    )
    second_key = build_scan_cache_key(
        directory=tmp_path / "two",
        effective_n_procs=2,
        effective_blacklist=(".git",),
        compute_hash=True,
        compute_stats=True,
        compute_frontmatter=True,
    )

    set_cached_scan_result(first_key, _make_result())

    assert get_cached_scan_result(second_key) is None


def test_clear_cache_removes_cached_entry(tmp_path: Path) -> None:
    key = build_scan_cache_key(
        directory=tmp_path,
        effective_n_procs=2,
        effective_blacklist=(".git",),
        compute_hash=True,
        compute_stats=True,
        compute_frontmatter=True,
    )
    set_cached_scan_result(key, _make_result())

    clear_cache()

    assert get_cached_scan_result(key) is None


def test_scan_uses_single_entry_cache(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "one.md").write_text("---\ntitle: One\n---\nBody", encoding="utf-8")

    first_result = scan_directory(project)
    (project / "two.md").write_text("---\ntitle: Two\n---\nBody", encoding="utf-8")
    second_result = scan_directory(project)

    assert first_result is second_result
    assert second_result.metadata.total_files == 1


def test_scan_force_refresh_bypasses_cache(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "one.md").write_text("---\ntitle: One\n---\nBody", encoding="utf-8")

    first_result = scan_directory(project)
    (project / "two.md").write_text("---\ntitle: Two\n---\nBody", encoding="utf-8")
    refreshed_result = scan_directory(project, force_refresh=True)

    assert first_result is not refreshed_result
    assert refreshed_result.metadata.total_files == 2


def test_clear_cache_invalidates_cached_scan_result(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "one.md").write_text("---\ntitle: One\n---\nBody", encoding="utf-8")

    first_result = scan_directory(project)
    (project / "two.md").write_text("---\ntitle: Two\n---\nBody", encoding="utf-8")

    clear_cache()
    second_result = scan_directory(project)

    assert first_result is not second_result
    assert second_result.metadata.total_files == 2


def test_scan_cache_key_includes_scan_options(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "one.md").write_text("---\ntitle: One\n---\nBody", encoding="utf-8")

    no_frontmatter_result = scan_directory(project, compute_frontmatter=False)
    with_frontmatter_result = scan_directory(project, compute_frontmatter=True)

    assert no_frontmatter_result is not with_frontmatter_result
    assert no_frontmatter_result.metadata.files_with_frontmatter is None
    assert with_frontmatter_result.metadata.files_with_frontmatter == 1
