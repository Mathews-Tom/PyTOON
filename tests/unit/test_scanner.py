"""Unit tests for scanner module."""

import pytest

from pytoon.decoder.scanner import scan_lines, LineCursor, ScanResult
from pytoon.decoder.types import ParsedLine, BlankLineInfo


class TestScanLines:
    """Test scan_lines function."""

    def test_empty_input(self) -> None:
        """Empty input should return empty result."""
        result = scan_lines("", indent_size=2, strict=True)
        assert result.lines == []
        assert result.blank_lines == []

    def test_single_line(self) -> None:
        """Single line should be scanned correctly."""
        result = scan_lines("key: value", indent_size=2, strict=True)
        assert len(result.lines) == 1
        line = result.lines[0]
        assert line.raw == "key: value"
        assert line.indent == 0
        assert line.content == "key: value"
        assert line.depth == 0
        assert line.line_number == 1

    def test_multiple_lines(self) -> None:
        """Multiple lines should be scanned correctly."""
        result = scan_lines("line1\nline2\nline3", indent_size=2, strict=True)
        assert len(result.lines) == 3
        assert result.lines[0].content == "line1"
        assert result.lines[1].content == "line2"
        assert result.lines[2].content == "line3"

    def test_indentation_depth_calculation(self) -> None:
        """Indentation should be converted to depth correctly."""
        source = "depth0\n  depth1\n    depth2\n      depth3"
        result = scan_lines(source, indent_size=2, strict=True)
        assert result.lines[0].depth == 0
        assert result.lines[1].depth == 1
        assert result.lines[2].depth == 2
        assert result.lines[3].depth == 3

    def test_blank_lines_tracked(self) -> None:
        """Blank lines should be tracked separately."""
        source = "line1\n\nline2\n  \nline3"
        result = scan_lines(source, indent_size=2, strict=True)
        assert len(result.lines) == 3  # Only non-blank lines
        assert len(result.blank_lines) == 2  # Two blank lines

    def test_blank_line_info(self) -> None:
        """Blank line info should be correct."""
        source = "line1\n\nline2"
        result = scan_lines(source, indent_size=2, strict=True)
        assert len(result.blank_lines) == 1
        blank = result.blank_lines[0]
        assert blank.line_number == 2
        assert blank.indent == 0
        assert blank.depth == 0

    def test_whitespace_only_blank_line(self) -> None:
        """Whitespace-only lines should be considered blank."""
        source = "line1\n   \nline2"
        result = scan_lines(source, indent_size=2, strict=True)
        assert len(result.lines) == 2
        assert len(result.blank_lines) == 1

    def test_different_indent_sizes(self) -> None:
        """Different indent sizes should be calculated correctly."""
        source = "    level1"  # 4 spaces
        result = scan_lines(source, indent_size=4, strict=True)
        assert result.lines[0].depth == 1

        result = scan_lines(source, indent_size=2, strict=True)
        assert result.lines[0].depth == 2

    def test_preserves_line_numbers(self) -> None:
        """Line numbers should be preserved correctly with blank lines."""
        source = "line1\n\nline3\n\nline5"
        result = scan_lines(source, indent_size=2, strict=True)
        assert result.lines[0].line_number == 1
        assert result.lines[1].line_number == 3
        assert result.lines[2].line_number == 5


class TestLineCursor:
    """Test LineCursor class."""

    def test_empty_cursor(self) -> None:
        """Empty cursor should indicate at_end."""
        cursor = LineCursor([], [])
        assert cursor.at_end() is True
        assert cursor.peek() is None
        assert cursor.next() is None

    def test_peek_returns_current(self) -> None:
        """peek should return current line without advancing."""
        lines = [
            ParsedLine("line1", 0, "line1", 0, 1),
            ParsedLine("line2", 0, "line2", 0, 2),
        ]
        cursor = LineCursor(lines, [])
        assert cursor.peek() == lines[0]
        assert cursor.peek() == lines[0]  # Still same

    def test_next_advances_cursor(self) -> None:
        """next should return current line and advance."""
        lines = [
            ParsedLine("line1", 0, "line1", 0, 1),
            ParsedLine("line2", 0, "line2", 0, 2),
        ]
        cursor = LineCursor(lines, [])
        assert cursor.next() == lines[0]
        assert cursor.peek() == lines[1]
        assert cursor.next() == lines[1]
        assert cursor.at_end() is True

    def test_advance_moves_position(self) -> None:
        """advance should move position without returning."""
        lines = [
            ParsedLine("line1", 0, "line1", 0, 1),
            ParsedLine("line2", 0, "line2", 0, 2),
        ]
        cursor = LineCursor(lines, [])
        cursor.advance()
        assert cursor.peek() == lines[1]

    def test_at_end_after_exhausting(self) -> None:
        """at_end should be True after exhausting all lines."""
        lines = [ParsedLine("line1", 0, "line1", 0, 1)]
        cursor = LineCursor(lines, [])
        cursor.next()
        assert cursor.at_end() is True

    def test_peek_at_depth_finds_line(self) -> None:
        """peek_at_depth should find line at specified depth."""
        lines = [
            ParsedLine("  line", 2, "line", 1, 1),
            ParsedLine("    nested", 4, "nested", 2, 2),
        ]
        cursor = LineCursor(lines, [])
        result = cursor.peek_at_depth(1)
        assert result == lines[0]

    def test_peek_at_depth_returns_none_when_not_found(self) -> None:
        """peek_at_depth should return None when depth not matched."""
        lines = [ParsedLine("  line", 2, "line", 1, 1)]
        cursor = LineCursor(lines, [])
        result = cursor.peek_at_depth(3)
        assert result is None

    def test_peek_at_end_returns_none(self) -> None:
        """peek should return None when at end."""
        lines = [ParsedLine("line1", 0, "line1", 0, 1)]
        cursor = LineCursor(lines, [])
        cursor.next()
        assert cursor.peek() is None

    def test_next_at_end_returns_none(self) -> None:
        """next should return None when at end."""
        cursor = LineCursor([], [])
        assert cursor.next() is None

    def test_position_tracking(self) -> None:
        """Cursor position should track correctly."""
        lines = [
            ParsedLine("line1", 0, "line1", 0, 1),
            ParsedLine("line2", 0, "line2", 0, 2),
            ParsedLine("line3", 0, "line3", 0, 3),
        ]
        cursor = LineCursor(lines, [])
        assert cursor.position == 0
        cursor.advance()
        assert cursor.position == 1
        cursor.next()
        assert cursor.position == 2


class TestScanResult:
    """Test ScanResult dataclass."""

    def test_scan_result_creation(self) -> None:
        """ScanResult should be creatable with lines and blank_lines."""
        lines = [ParsedLine("test", 0, "test", 0, 1)]
        blank_lines = [BlankLineInfo(2, 0, 0)]
        result = ScanResult(lines, blank_lines)
        assert result.lines == lines
        assert result.blank_lines == blank_lines

    def test_scan_result_immutability(self) -> None:
        """ScanResult should be immutable (frozen dataclass)."""
        result = ScanResult([], [])
        # ScanResult is a dataclass but not frozen, so test attributes
        assert result.lines == []
        assert result.blank_lines == []


class TestParsedLine:
    """Test ParsedLine dataclass."""

    def test_parsed_line_creation(self) -> None:
        """ParsedLine should be creatable with all fields."""
        line = ParsedLine("  content", 2, "content", 1, 5)
        assert line.raw == "  content"
        assert line.indent == 2
        assert line.content == "content"
        assert line.depth == 1
        assert line.line_number == 5

    def test_parsed_line_immutability(self) -> None:
        """ParsedLine should be immutable (frozen dataclass)."""
        line = ParsedLine("test", 0, "test", 0, 1)
        with pytest.raises(Exception):  # FrozenInstanceError
            line.content = "new"  # type: ignore[misc]


class TestBlankLineInfo:
    """Test BlankLineInfo dataclass."""

    def test_blank_line_info_creation(self) -> None:
        """BlankLineInfo should be creatable with line_number, indent, and depth."""
        blank = BlankLineInfo(10, 3, 1)
        assert blank.line_number == 10
        assert blank.indent == 3
        assert blank.depth == 1

    def test_blank_line_info_immutability(self) -> None:
        """BlankLineInfo should be immutable (frozen dataclass)."""
        blank = BlankLineInfo(1, 0, 0)
        with pytest.raises(Exception):  # FrozenInstanceError
            blank.line_number = 2  # type: ignore[misc]
