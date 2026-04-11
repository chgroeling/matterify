"""File hashing utilities."""

import hashlib


def _compute_file_hash(content: bytes) -> str | None:
    """Compute SHA-256 hash of file content.

    Args:
        content: The file content as bytes.

    Returns:
        Hex string of SHA-256 hash, or None on error.
    """
    try:
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None
