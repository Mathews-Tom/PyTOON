"""Scanner for TOON source with depth computation.

This module pre-processes TOON input to compute depth information
for each line, enabling depth-based parsing per TOON v2.0 spec.
"""

from __future__ import annotations

from pytoon.decoder.types import BlankLineInfo, ParsedLine
from pytoon.utils.errors import TOONDecodeError


class ScanResult:
    """Result of scanning TOON input.

    Attributes:
        lines: List of parsed non-blank lines with depth info
        blank_lines: List of blank line information for validation
    """

    def __init__(
        self, lines: list[ParsedLine], blank_lines: list[BlankLineInfo]
    ) -> None:
        """Initialize scan result.

        Args:
            lines: Parsed non-blank lines
            blank_lines: Blank line tracking info
        """
        self.lines = lines
        self.blank_lines = blank_lines


class LineCursor:
    """Cursor for navigating parsed lines with depth awareness.

    Provides peek-ahead and depth-based filtering capabilities
    for recursive descent parsing.
    """

    def __init__(
        self,
        lines: list[ParsedLine],
        blank_lines: list[BlankLineInfo] | None = None,
    ) -> None:
        """Initialize cursor.

        Args:
            lines: List of parsed lines to navigate
            blank_lines: Optional blank line tracking
        """
        self._lines = lines
        self._index = 0
        self._blank_lines = blank_lines or []

    def peek(self) -> ParsedLine | None:
        """Look at current line without advancing.

        Returns:
            Current line or None if at end
        """
        if self._index < len(self._lines):
            return self._lines[self._index]
        return None

    def next(self) -> ParsedLine | None:
        """Get current line and advance cursor.

        Returns:
            Current line or None if at end
        """
        if self._index < len(self._lines):
            line = self._lines[self._index]
            self._index += 1
            return line
        return None

    def current(self) -> ParsedLine | None:
        """Get the last consumed line.

        Returns:
            Last consumed line or None if nothing consumed
        """
        if self._index > 0:
            return self._lines[self._index - 1]
        return None

    def advance(self) -> None:
        """Move cursor forward by one position."""
        if self._index < len(self._lines):
            self._index += 1

    def at_end(self) -> bool:
        """Check if cursor is at end of lines.

        Returns:
            True if no more lines to process
        """
        return self._index >= len(self._lines)

    def peek_at_depth(self, target_depth: int) -> ParsedLine | None:
        """Peek if next line matches target depth.

        Args:
            target_depth: Expected depth to match

        Returns:
            Line if depth matches, None otherwise
        """
        line = self.peek()
        if line and line.depth == target_depth:
            return line
        return None

    @property
    def blank_lines(self) -> list[BlankLineInfo]:
        """Get tracked blank lines.

        Returns:
            List of blank line information
        """
        return self._blank_lines

    @property
    def position(self) -> int:
        """Get current cursor position.

        Returns:
            Current index in line list
        """
        return self._index


def scan_lines(source: str, indent_size: int, strict: bool) -> ScanResult:
    """Scan TOON source into parsed lines with depth computation.

    Args:
        source: TOON source string
        indent_size: Number of spaces per indentation level
        strict: Enable strict validation (tabs and indent multiples)

    Returns:
        ScanResult with parsed lines and blank line tracking

    Raises:
        TOONDecodeError: If indentation is invalid in strict mode
    """
    if not source.strip():
        return ScanResult([], [])

    raw_lines = source.split("\n")
    parsed: list[ParsedLine] = []
    blank_lines: list[BlankLineInfo] = []

    for i, raw in enumerate(raw_lines):
        line_number = i + 1

        # Count leading spaces
        indent = 0
        while indent < len(raw) and raw[indent] == " ":
            indent += 1

        content = raw[indent:]

        # Track blank lines separately (empty or only whitespace)
        if not content.strip():
            depth = indent // indent_size if indent_size > 0 else 0
            blank_lines.append(BlankLineInfo(line_number, indent, depth))
            continue

        # Compute depth
        depth = indent // indent_size if indent_size > 0 else 0

        # Strict mode validation
        if strict:
            # Check for tabs in indentation
            if "\t" in raw[:indent]:
                raise TOONDecodeError(
                    f"Line {line_number}: Tabs are not allowed in indentation"
                )

            # Check for exact multiples of indent_size
            if indent > 0 and indent_size > 0 and indent % indent_size != 0:
                raise TOONDecodeError(
                    f"Line {line_number}: Indentation must be exact multiple of "
                    f"{indent_size}, but found {indent} spaces"
                )

        parsed.append(ParsedLine(raw, indent, content, depth, line_number))

    return ScanResult(parsed, blank_lines)
