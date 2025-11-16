"""Type definitions for TOON decoder with depth tracking.

This module provides data structures for parsing TOON with proper
indentation awareness as required by TOON v2.0 specification.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedLine:
    """A single parsed line with computed metadata.

    Attributes:
        raw: Original line text including indentation
        indent: Number of leading spaces
        content: Content after indentation (stripped of leading spaces)
        depth: Computed depth (indent // indent_size)
        line_number: 1-based line number for error messages
    """

    raw: str
    indent: int
    content: str
    depth: int
    line_number: int


@dataclass(frozen=True)
class BlankLineInfo:
    """Track blank lines for validation.

    Attributes:
        line_number: 1-based line number
        indent: Number of leading spaces (may have trailing spaces)
        depth: Computed depth based on indentation
    """

    line_number: int
    indent: int
    depth: int


@dataclass(frozen=True)
class ArrayHeaderInfo:
    """Parsed array header information.

    Attributes:
        key: Optional key name (None for root arrays)
        length: Declared array length
        delimiter: Active delimiter character (',' or '\\t' or '|')
        fields: Optional list of field names for tabular arrays
    """

    key: str | None
    length: int
    delimiter: str
    fields: list[str] | None
