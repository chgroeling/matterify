"""Public type aliases for matterify."""

from collections.abc import Callable

type ContentCallback = Callable[[str], object | None]
