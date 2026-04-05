"""In-memory cache utilities for scan results."""

from pathlib import Path
from threading import Lock

from matterify.models import AggregatedResult

type ScanCacheKey = tuple[str, int, tuple[str, ...], bool, bool, bool]

_SCAN_CACHE_LOCK = Lock()
_SCAN_CACHE_KEY: ScanCacheKey | None = None
_SCAN_CACHE_RESULT: AggregatedResult | None = None


def build_scan_cache_key(
    directory: Path,
    effective_n_procs: int,
    effective_blacklist: tuple[str, ...],
    compute_hash: bool,
    compute_stats: bool,
    compute_frontmatter: bool,
) -> ScanCacheKey:
    """Build a stable cache key for single-entry scan result caching."""
    normalized_directory = str(directory.resolve())
    normalized_blacklist = tuple(sorted(effective_blacklist))

    return (
        normalized_directory,
        effective_n_procs,
        normalized_blacklist,
        compute_hash,
        compute_stats,
        compute_frontmatter,
    )


def get_cached_scan_result(cache_key: ScanCacheKey) -> AggregatedResult | None:
    """Return cached scan result for key if available."""
    with _SCAN_CACHE_LOCK:
        if cache_key == _SCAN_CACHE_KEY:
            return _SCAN_CACHE_RESULT

    return None


def set_cached_scan_result(cache_key: ScanCacheKey, result: AggregatedResult) -> None:
    """Replace the single-entry in-memory scan cache."""
    global _SCAN_CACHE_KEY
    global _SCAN_CACHE_RESULT

    with _SCAN_CACHE_LOCK:
        _SCAN_CACHE_KEY = cache_key
        _SCAN_CACHE_RESULT = result


def clear_cache() -> None:
    """Clear the in-memory single-entry cache for scan results."""
    global _SCAN_CACHE_KEY
    global _SCAN_CACHE_RESULT

    with _SCAN_CACHE_LOCK:
        _SCAN_CACHE_KEY = None
        _SCAN_CACHE_RESULT = None
