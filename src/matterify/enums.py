"""Enumeration types for matterify."""

from enum import Enum


class FileStatus(Enum):
    """Processing status for a single file."""

    OK = "ok"
    ILLEGAL = "illegal"


class FileError(Enum):
    """Error codes for illegal file status."""

    NO_FRONTMATTER = "no_frontmatter"
    YAML_PARSE_ERROR = "yaml_parse_error"
    NON_DICT_FRONTMATTER = "non_dict_frontmatter"
    DECODE_ERROR = "decode_error"
