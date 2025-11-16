"""Unit tests for parser utilities module."""

import pytest

from pytoon.decoder.parser_utils import (
    parse_array_header,
    parse_bracket_segment,
    parse_delimited_values,
    parse_primitive_token,
    unescape_string,
    parse_key_token,
    find_closing_quote,
)
from pytoon.utils.errors import TOONDecodeError


class TestParseArrayHeader:
    """Test parse_array_header function."""

    def test_simple_header(self) -> None:
        """Simple array header should parse correctly."""
        result = parse_array_header("[3]:")
        assert result is not None
        header, inline = result
        assert header.key is None
        assert header.length == 3
        assert header.delimiter == ","
        assert header.fields is None
        assert inline is None

    def test_header_with_key(self) -> None:
        """Array header with key should parse correctly."""
        result = parse_array_header("items[3]:")
        assert result is not None
        header, inline = result
        assert header.key == "items"
        assert header.length == 3

    def test_header_with_fields(self) -> None:
        """Array header with fields should parse correctly."""
        result = parse_array_header("[2]{id,name}:")
        assert result is not None
        header, inline = result
        assert header.length == 2
        assert header.fields == ["id", "name"]

    def test_header_with_inline_values(self) -> None:
        """Array header with inline values should extract them."""
        result = parse_array_header("[3]: 1,2,3")
        assert result is not None
        header, inline = result
        assert header.length == 3
        assert inline == "1,2,3"

    def test_header_tab_delimiter(self) -> None:
        """Array header with tab delimiter should parse correctly."""
        result = parse_array_header("[3\t]:")
        assert result is not None
        header, _ = result
        assert header.delimiter == "\t"

    def test_header_pipe_delimiter(self) -> None:
        """Array header with pipe delimiter should parse correctly."""
        result = parse_array_header("[3|]:")
        assert result is not None
        header, _ = result
        assert header.delimiter == "|"

    def test_not_an_array_header(self) -> None:
        """Non-array header should return None."""
        assert parse_array_header("key: value") is None
        assert parse_array_header("just text") is None
        assert parse_array_header("") is None

    def test_incomplete_header(self) -> None:
        """Incomplete header should return None."""
        assert parse_array_header("[3") is None
        assert parse_array_header("[3]") is None  # Missing colon


class TestParseBracketSegment:
    """Test parse_bracket_segment function."""

    def test_simple_number(self) -> None:
        """Simple number should parse correctly."""
        length, delimiter = parse_bracket_segment("3", ",")
        assert length == 3
        assert delimiter == ","

    def test_number_with_spaces(self) -> None:
        """Number with spaces should parse correctly."""
        length, delimiter = parse_bracket_segment("  5  ", ",")
        assert length == 5

    def test_tab_delimiter_suffix(self) -> None:
        """Tab delimiter suffix should be detected."""
        length, delimiter = parse_bracket_segment("3\t", ",")
        assert length == 3
        assert delimiter == "\t"

    def test_pipe_delimiter_suffix(self) -> None:
        """Pipe delimiter suffix should be detected."""
        length, delimiter = parse_bracket_segment("3|", ",")
        assert length == 3
        assert delimiter == "|"

    def test_invalid_number_raises_error(self) -> None:
        """Invalid number should raise TOONDecodeError."""
        with pytest.raises(TOONDecodeError, match="Invalid array header"):
            parse_bracket_segment("abc", ",")

    def test_negative_number_raises_error(self) -> None:
        """Negative number should raise TOONDecodeError."""
        with pytest.raises(TOONDecodeError, match="Array length cannot be negative"):
            parse_bracket_segment("-1", ",")


class TestParseDelimitedValues:
    """Test parse_delimited_values function."""

    def test_comma_separated(self) -> None:
        """Comma-separated values should parse correctly."""
        result = parse_delimited_values("1,2,3", ",")
        assert result == ["1", "2", "3"]

    def test_tab_separated(self) -> None:
        """Tab-separated values should parse correctly."""
        result = parse_delimited_values("a\tb\tc", "\t")
        assert result == ["a", "b", "c"]

    def test_pipe_separated(self) -> None:
        """Pipe-separated values should parse correctly."""
        result = parse_delimited_values("x|y|z", "|")
        assert result == ["x", "y", "z"]

    def test_values_with_spaces(self) -> None:
        """Values with surrounding spaces should be trimmed."""
        result = parse_delimited_values(" a , b , c ", ",")
        assert result == ["a", "b", "c"]

    def test_quoted_values(self) -> None:
        """Quoted values should preserve delimiters inside quotes."""
        result = parse_delimited_values('"hello,world",test', ",")
        assert result == ['"hello,world"', "test"]

    def test_quoted_with_escapes(self) -> None:
        """Quoted values with escapes should handle correctly."""
        result = parse_delimited_values('"say \\"hi\\"",other', ",")
        assert result == ['"say \\"hi\\""', "other"]

    def test_empty_string(self) -> None:
        """Empty string should return empty list."""
        result = parse_delimited_values("", ",")
        assert result == []

    def test_single_value(self) -> None:
        """Single value without delimiter should return as list."""
        result = parse_delimited_values("single", ",")
        assert result == ["single"]


class TestParsePrimitiveToken:
    """Test parse_primitive_token function."""

    def test_null(self) -> None:
        """null token should return None."""
        assert parse_primitive_token("null") is None
        assert parse_primitive_token("  null  ") is None

    def test_boolean_true(self) -> None:
        """true token should return True."""
        assert parse_primitive_token("true") is True
        assert parse_primitive_token("  true  ") is True

    def test_boolean_false(self) -> None:
        """false token should return False."""
        assert parse_primitive_token("false") is False

    def test_integer(self) -> None:
        """Integer tokens should parse correctly."""
        assert parse_primitive_token("42") == 42
        assert parse_primitive_token("-123") == -123
        assert parse_primitive_token("0") == 0

    def test_float(self) -> None:
        """Float tokens should parse correctly."""
        assert parse_primitive_token("3.14") == 3.14
        assert parse_primitive_token("-2.5") == -2.5
        assert parse_primitive_token("0.5") == 0.5

    def test_quoted_string(self) -> None:
        """Quoted strings should unescape and return."""
        assert parse_primitive_token('"hello"') == "hello"
        assert parse_primitive_token('"with space"') == "with space"
        assert parse_primitive_token('"say \\"hi\\""') == 'say "hi"'

    def test_unquoted_string(self) -> None:
        """Unquoted strings should return as-is."""
        assert parse_primitive_token("hello") == "hello"
        assert parse_primitive_token("word123") == "word123"


class TestUnescapeString:
    """Test unescape_string function."""

    def test_no_escapes(self) -> None:
        """String without escapes should return unchanged."""
        assert unescape_string("hello") == "hello"

    def test_escaped_quote(self) -> None:
        """Escaped quotes should be unescaped."""
        assert unescape_string('say \\"hi\\"') == 'say "hi"'

    def test_escaped_backslash(self) -> None:
        """Escaped backslashes should be unescaped."""
        assert unescape_string("path\\\\file") == "path\\file"

    def test_escaped_newline(self) -> None:
        """Escaped newlines should be unescaped."""
        assert unescape_string("line1\\nline2") == "line1\nline2"

    def test_escaped_tab(self) -> None:
        """Escaped tabs should be unescaped."""
        assert unescape_string("col1\\tcol2") == "col1\tcol2"

    def test_mixed_escapes(self) -> None:
        """Multiple escape sequences should all be handled."""
        result = unescape_string('test\\"\\n\\t\\\\')
        assert result == 'test"\n\t\\'


class TestParseKeyToken:
    """Test parse_key_token function."""

    def test_simple_key(self) -> None:
        """Simple key should parse correctly."""
        key, end_pos, quoted = parse_key_token("name: value", 0)
        assert key == "name"
        assert end_pos == 5  # Position after ": "
        assert quoted is False

    def test_key_with_underscores(self) -> None:
        """Key with underscores should parse correctly."""
        key, end_pos, quoted = parse_key_token("my_key: value", 0)
        assert key == "my_key"
        assert quoted is False

    def test_key_with_numbers(self) -> None:
        """Key with numbers should parse correctly."""
        key, end_pos, quoted = parse_key_token("key123: value", 0)
        assert key == "key123"

    def test_quoted_key(self) -> None:
        """Quoted key should parse correctly."""
        key, end_pos, quoted = parse_key_token('"spaced key": value', 0)
        assert key == "spaced key"
        assert quoted is True

    def test_quoted_key_with_escapes(self) -> None:
        """Quoted key with escapes should unescape."""
        key, end_pos, quoted = parse_key_token('"key\\"test": value', 0)
        assert key == 'key"test'
        assert quoted is True

    def test_key_no_space_after_colon(self) -> None:
        """Key without space after colon should still parse."""
        key, end_pos, quoted = parse_key_token("key:value", 0)
        assert key == "key"
        assert end_pos == 4  # Position after ":"


class TestFindClosingQuote:
    """Test find_closing_quote function."""

    def test_simple_quote(self) -> None:
        """Simple quoted string should find closing quote."""
        pos = find_closing_quote('"hello"', 0)
        assert pos == 6

    def test_escaped_quote(self) -> None:
        """Escaped quote should not be closing quote."""
        pos = find_closing_quote('"say \\"hi\\""', 0)
        assert pos == 11  # Position of closing "

    def test_escaped_backslash_before_quote(self) -> None:
        """Escaped backslash before quote should handle correctly."""
        pos = find_closing_quote('"test\\\\"', 0)
        assert pos == 7

    def test_no_closing_quote(self) -> None:
        """Missing closing quote should return -1."""
        pos = find_closing_quote('"unclosed', 0)
        assert pos == -1

    def test_start_position(self) -> None:
        """Start position should be respected."""
        pos = find_closing_quote('xxx"test"', 3)
        assert pos == 8
