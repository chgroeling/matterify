"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_md_with_frontmatter(tmp_path: Path) -> Path:
    """Create a temporary Markdown file with YAML frontmatter."""
    content = """---
title: Test Document
author: Test Author
tags:
  - test
  - example
---

# Hello World

This is test content.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_md_without_frontmatter(tmp_path: Path) -> Path:
    """Create a temporary Markdown file without frontmatter."""
    content = """# No Frontmatter

This file has no YAML frontmatter.
"""
    file_path = tmp_path / "no_frontmatter.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with multiple Markdown files."""
    project = tmp_path / "project"
    project.mkdir()

    (project / "readme.md").write_text(
        "---\ntitle: README\nversion: 1.0.0\n---\n\n# Project\n",
        encoding="utf-8",
    )

    sub = project / "docs"
    sub.mkdir()
    (sub / "guide.md").write_text(
        "---\ntitle: Guide\nauthor: Admin\n---\n\n# Guide\n",
        encoding="utf-8",
    )

    (project / "notes.txt").write_text("Not a markdown file", encoding="utf-8")

    return project
