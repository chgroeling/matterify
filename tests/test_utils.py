"""Tests for utility modules."""

from matterify import __version__


def test_version_is_string() -> None:
    assert isinstance(__version__, str)


def test_version_format() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts[:2])
