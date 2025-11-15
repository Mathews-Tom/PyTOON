"""Common validation helper functions for PyToon.

This module provides validation utilities for configuration parameters
and identifiers. These functions provide consistent error messages and
can be used throughout the PyToon codebase.
"""

from __future__ import annotations

import re
from typing import Final

# Safe identifier pattern for key folding
# More restrictive than general identifiers - no leading underscores
# to avoid folding private keys accidentally
_SAFE_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_]*$"
)

# Supported delimiters for tabular arrays
_SUPPORTED_DELIMITERS: Final[tuple[str, ...]] = (",", "\t", "|")


def validate_indent(indent: int) -> None:
    """Validate that indentation is a positive integer.

    This function ensures the indentation value is valid for TOON encoding.
    Indentation must be at least 1 space.

    Args:
        indent: Number of spaces per indentation level.

    Raises:
        ValueError: If indent is not a positive integer (indent <= 0).

    Examples:
        >>> validate_indent(2)  # Valid, no error
        >>> validate_indent(4)  # Valid, no error
        >>> validate_indent(1)  # Valid, minimum
        >>> validate_indent(0)
        Traceback (most recent call last):
            ...
        ValueError: indent must be a positive integer, got: 0
        >>> validate_indent(-1)
        Traceback (most recent call last):
            ...
        ValueError: indent must be a positive integer, got: -1
    """
    if indent <= 0:
        raise ValueError(f"indent must be a positive integer, got: {indent}")


def validate_delimiter(delimiter: str) -> None:
    """Validate that delimiter is a supported TOON delimiter.

    TOON supports three delimiters for tabular arrays:
    - Comma (',') - default, most compact
    - Tab ('\\t') - useful for TSV-like data
    - Pipe ('|') - useful for visual separation

    Args:
        delimiter: Field delimiter string to validate.

    Raises:
        ValueError: If delimiter is not one of ',', '\\t', or '|'.

    Examples:
        >>> validate_delimiter(',')  # Valid, no error
        >>> validate_delimiter('\\t')  # Valid, no error
        >>> validate_delimiter('|')  # Valid, no error
        >>> validate_delimiter(';')
        Traceback (most recent call last):
            ...
        ValueError: delimiter must be one of ',', '\\t', '|', got: ';'
        >>> validate_delimiter('  ')
        Traceback (most recent call last):
            ...
        ValueError: delimiter must be one of ',', '\\t', '|', got: '  '
    """
    if delimiter not in _SUPPORTED_DELIMITERS:
        valid_str = ", ".join(repr(d) for d in _SUPPORTED_DELIMITERS)
        raise ValueError(f"delimiter must be one of {valid_str}, got: {delimiter!r}")


def is_safe_identifier(key: str) -> bool:
    """Check if a key is safe for key folding operations.

    A safe identifier for key folding:
    - Starts with a letter (not underscore, to avoid folding private keys)
    - Contains only letters, digits, or underscores
    - Does NOT contain dots (would cause ambiguity in folded paths)
    - Is not empty

    This is more restrictive than general TOON identifiers because
    key folding creates dotted paths like "a.b.c", and we need to avoid
    ambiguity when expanding them back.

    Args:
        key: Key string to check for safe folding.

    Returns:
        True if the key is safe for folding, False otherwise.

    Examples:
        >>> is_safe_identifier('name')
        True
        >>> is_safe_identifier('userId')
        True
        >>> is_safe_identifier('item_count')
        True
        >>> is_safe_identifier('data2')
        True
        >>> is_safe_identifier('_private')  # Leading underscore not safe
        False
        >>> is_safe_identifier('key.name')  # Contains dot
        False
        >>> is_safe_identifier('123key')  # Starts with digit
        False
        >>> is_safe_identifier('')  # Empty string
        False
        >>> is_safe_identifier('key-name')  # Contains dash
        False
        >>> is_safe_identifier('key name')  # Contains space
        False
    """
    if not key:
        return False

    # Check for dots (would cause ambiguity in folded paths)
    if "." in key:
        return False

    # Check against safe identifier pattern
    return bool(_SAFE_IDENTIFIER_PATTERN.match(key))


def validate_key_folding_mode(mode: str) -> None:
    """Validate that key folding mode is supported.

    Args:
        mode: Key folding mode to validate.

    Raises:
        ValueError: If mode is not 'off' or 'safe'.

    Examples:
        >>> validate_key_folding_mode('off')  # Valid, no error
        >>> validate_key_folding_mode('safe')  # Valid, no error
        >>> validate_key_folding_mode('auto')
        Traceback (most recent call last):
            ...
        ValueError: key_folding must be one of 'off', 'safe', got: 'auto'
    """
    valid_modes = ("off", "safe")
    if mode not in valid_modes:
        valid_str = ", ".join(repr(m) for m in valid_modes)
        raise ValueError(f"key_folding must be one of {valid_str}, got: {mode!r}")


def validate_expand_paths_mode(mode: str) -> None:
    """Validate that path expansion mode is supported.

    Args:
        mode: Path expansion mode to validate.

    Raises:
        ValueError: If mode is not 'off' or 'safe'.

    Examples:
        >>> validate_expand_paths_mode('off')  # Valid, no error
        >>> validate_expand_paths_mode('safe')  # Valid, no error
        >>> validate_expand_paths_mode('auto')
        Traceback (most recent call last):
            ...
        ValueError: expand_paths must be one of 'off', 'safe', got: 'auto'
    """
    valid_modes = ("off", "safe")
    if mode not in valid_modes:
        valid_str = ", ".join(repr(m) for m in valid_modes)
        raise ValueError(f"expand_paths must be one of {valid_str}, got: {mode!r}")
