"""Unit tests for TOONSpec class."""

import re

import pytest

from pytoon.core.spec import TOONSpec


class TestTOONSpecConstants:
    """Test TOON specification constants."""

    def test_version_is_1_5(self) -> None:
        """VERSION should be 1.5."""
        assert TOONSpec.VERSION == "1.5"

    def test_default_indent_is_2(self) -> None:
        """DEFAULT_INDENT should be 2."""
        assert TOONSpec.DEFAULT_INDENT == 2

    def test_min_indent_is_1(self) -> None:
        """MIN_INDENT should be 1."""
        assert TOONSpec.MIN_INDENT == 1

    def test_max_indent_is_8(self) -> None:
        """MAX_INDENT should be 8."""
        assert TOONSpec.MAX_INDENT == 8

    def test_supported_delimiters(self) -> None:
        """SUPPORTED_DELIMITERS should include comma, tab, pipe."""
        assert TOONSpec.SUPPORTED_DELIMITERS == [",", "\t", "|"]

    def test_default_delimiter_is_comma(self) -> None:
        """DEFAULT_DELIMITER should be comma."""
        assert TOONSpec.DEFAULT_DELIMITER == ","

    def test_boolean_values(self) -> None:
        """BOOLEAN_VALUES should map true/false strings."""
        assert TOONSpec.BOOLEAN_VALUES == {"true": True, "false": False}

    def test_null_value(self) -> None:
        """NULL_VALUE should be 'null'."""
        assert TOONSpec.NULL_VALUE == "null"

    def test_key_folding_modes(self) -> None:
        """KEY_FOLDING_MODES should include 'off' and 'safe'."""
        assert TOONSpec.KEY_FOLDING_MODES == ["off", "safe"]

    def test_reserved_tokens(self) -> None:
        """RESERVED_TOKENS should include true, false, null."""
        assert TOONSpec.RESERVED_TOKENS == {"true", "false", "null"}

    def test_max_nesting_depth(self) -> None:
        """MAX_NESTING_DEPTH should be 100."""
        assert TOONSpec.MAX_NESTING_DEPTH == 100

    def test_max_array_length(self) -> None:
        """MAX_ARRAY_LENGTH should be 1_000_000."""
        assert TOONSpec.MAX_ARRAY_LENGTH == 1_000_000


class TestIdentifierPattern:
    """Test identifier pattern validation."""

    def test_valid_simple_identifier(self) -> None:
        """Simple identifiers should match."""
        assert TOONSpec.is_valid_identifier("name")
        assert TOONSpec.is_valid_identifier("user_id")
        assert TOONSpec.is_valid_identifier("_private")
        assert TOONSpec.is_valid_identifier("item2")

    def test_valid_single_letter(self) -> None:
        """Single letter should be valid."""
        assert TOONSpec.is_valid_identifier("a")
        assert TOONSpec.is_valid_identifier("Z")

    def test_valid_underscore_start(self) -> None:
        """Identifiers starting with underscore should be valid."""
        assert TOONSpec.is_valid_identifier("_")
        assert TOONSpec.is_valid_identifier("__init__")
        assert TOONSpec.is_valid_identifier("_private_var")

    def test_invalid_starts_with_digit(self) -> None:
        """Identifiers starting with digit should be invalid."""
        assert not TOONSpec.is_valid_identifier("123key")
        assert not TOONSpec.is_valid_identifier("1st")
        assert not TOONSpec.is_valid_identifier("0x00")

    def test_invalid_contains_dot(self) -> None:
        """Identifiers with dots should be invalid."""
        assert not TOONSpec.is_valid_identifier("key.name")
        assert not TOONSpec.is_valid_identifier("a.b.c")

    def test_invalid_contains_dash(self) -> None:
        """Identifiers with dashes should be invalid."""
        assert not TOONSpec.is_valid_identifier("key-name")
        assert not TOONSpec.is_valid_identifier("my-var")

    def test_invalid_contains_space(self) -> None:
        """Identifiers with spaces should be invalid."""
        assert not TOONSpec.is_valid_identifier("key name")
        assert not TOONSpec.is_valid_identifier(" name")
        assert not TOONSpec.is_valid_identifier("name ")

    def test_invalid_empty_string(self) -> None:
        """Empty string should be invalid."""
        assert not TOONSpec.is_valid_identifier("")

    def test_invalid_special_characters(self) -> None:
        """Identifiers with special characters should be invalid."""
        assert not TOONSpec.is_valid_identifier("key@value")
        assert not TOONSpec.is_valid_identifier("key#value")
        assert not TOONSpec.is_valid_identifier("key$value")


class TestArrayHeaderPattern:
    """Test array header pattern matching."""

    def test_simple_array_header(self) -> None:
        """Simple array header should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[3]:")
        assert match is not None
        assert match.group(1) == "3"
        assert match.group(2) is None

    def test_empty_array_header(self) -> None:
        """Empty array header should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[0]:")
        assert match is not None
        assert match.group(1) == "0"

    def test_large_array_header(self) -> None:
        """Large array header should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[1000]:")
        assert match is not None
        assert match.group(1) == "1000"

    def test_tabular_array_header(self) -> None:
        """Tabular array header should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[2]{id,name}:")
        assert match is not None
        assert match.group(1) == "2"
        assert match.group(2) == "id,name"

    def test_tabular_with_spaces(self) -> None:
        """Tabular header with spaces in fields should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[3]{a, b, c}:")
        assert match is not None
        assert match.group(2) == "a, b, c"

    def test_header_without_colon(self) -> None:
        """Header without colon should match."""
        match = TOONSpec.ARRAY_HEADER_PATTERN.match("[5]")
        assert match is not None
        assert match.group(1) == "5"


class TestNumericPatterns:
    """Test numeric pattern matching."""

    def test_integer_pattern_positive(self) -> None:
        """Positive integers should match."""
        assert TOONSpec.INTEGER_PATTERN.match("0")
        assert TOONSpec.INTEGER_PATTERN.match("42")
        assert TOONSpec.INTEGER_PATTERN.match("1000000")

    def test_integer_pattern_negative(self) -> None:
        """Negative integers should match."""
        assert TOONSpec.INTEGER_PATTERN.match("-1")
        assert TOONSpec.INTEGER_PATTERN.match("-42")
        assert TOONSpec.INTEGER_PATTERN.match("-1000000")

    def test_integer_pattern_rejects_float(self) -> None:
        """Floats should not match integer pattern."""
        assert not TOONSpec.INTEGER_PATTERN.match("3.14")
        assert not TOONSpec.INTEGER_PATTERN.match("-2.5")

    def test_float_pattern_positive(self) -> None:
        """Positive floats should match."""
        assert TOONSpec.FLOAT_PATTERN.match("3.14")
        assert TOONSpec.FLOAT_PATTERN.match("0.5")
        assert TOONSpec.FLOAT_PATTERN.match("100.001")

    def test_float_pattern_negative(self) -> None:
        """Negative floats should match."""
        assert TOONSpec.FLOAT_PATTERN.match("-3.14")
        assert TOONSpec.FLOAT_PATTERN.match("-0.5")

    def test_float_pattern_rejects_integer(self) -> None:
        """Integers should not match float pattern."""
        assert not TOONSpec.FLOAT_PATTERN.match("42")
        assert not TOONSpec.FLOAT_PATTERN.match("-10")

    def test_float_pattern_rejects_scientific(self) -> None:
        """Scientific notation should not match."""
        assert not TOONSpec.FLOAT_PATTERN.match("1e6")
        assert not TOONSpec.FLOAT_PATTERN.match("3.14e2")


class TestReservedToken:
    """Test reserved token checking."""

    def test_true_is_reserved(self) -> None:
        """'true' should be reserved."""
        assert TOONSpec.is_reserved_token("true")

    def test_false_is_reserved(self) -> None:
        """'false' should be reserved."""
        assert TOONSpec.is_reserved_token("false")

    def test_null_is_reserved(self) -> None:
        """'null' should be reserved."""
        assert TOONSpec.is_reserved_token("null")

    def test_case_insensitive(self) -> None:
        """Reserved token check should be case-insensitive."""
        assert TOONSpec.is_reserved_token("TRUE")
        assert TOONSpec.is_reserved_token("False")
        assert TOONSpec.is_reserved_token("NULL")

    def test_non_reserved_words(self) -> None:
        """Non-reserved words should return False."""
        assert not TOONSpec.is_reserved_token("hello")
        assert not TOONSpec.is_reserved_token("name")
        assert not TOONSpec.is_reserved_token("truthy")


class TestRequiresQuoting:
    """Test string quoting requirement detection."""

    def test_empty_string_requires_quoting(self) -> None:
        """Empty strings should require quoting."""
        assert TOONSpec.requires_quoting("")

    def test_simple_string_no_quoting(self) -> None:
        """Simple strings should not require quoting."""
        assert not TOONSpec.requires_quoting("hello")
        assert not TOONSpec.requires_quoting("world")

    def test_leading_whitespace_requires_quoting(self) -> None:
        """Leading whitespace should require quoting."""
        assert TOONSpec.requires_quoting(" hello")
        assert TOONSpec.requires_quoting("  world")

    def test_trailing_whitespace_requires_quoting(self) -> None:
        """Trailing whitespace should require quoting."""
        assert TOONSpec.requires_quoting("hello ")
        assert TOONSpec.requires_quoting("world  ")

    def test_comma_requires_quoting(self) -> None:
        """Commas should require quoting."""
        assert TOONSpec.requires_quoting("hello, world")

    def test_tab_requires_quoting(self) -> None:
        """Tabs should require quoting."""
        assert TOONSpec.requires_quoting("hello\tworld")

    def test_pipe_requires_quoting(self) -> None:
        """Pipes should require quoting."""
        assert TOONSpec.requires_quoting("a|b")

    def test_colon_requires_quoting(self) -> None:
        """Colons should require quoting."""
        assert TOONSpec.requires_quoting("key:value")

    def test_brackets_require_quoting(self) -> None:
        """Brackets should require quoting."""
        assert TOONSpec.requires_quoting("[array]")
        assert TOONSpec.requires_quoting("{object}")

    def test_newline_requires_quoting(self) -> None:
        """Newlines should require quoting."""
        assert TOONSpec.requires_quoting("line1\nline2")

    def test_quote_requires_quoting(self) -> None:
        """Quotes should require quoting."""
        assert TOONSpec.requires_quoting('he said "hi"')

    def test_backslash_requires_quoting(self) -> None:
        """Backslashes should require quoting."""
        assert TOONSpec.requires_quoting("path\\to\\file")

    def test_boolean_string_requires_quoting(self) -> None:
        """Boolean-like strings should require quoting."""
        assert TOONSpec.requires_quoting("true")
        assert TOONSpec.requires_quoting("false")

    def test_null_string_requires_quoting(self) -> None:
        """Null-like string should require quoting."""
        assert TOONSpec.requires_quoting("null")

    def test_numeric_string_requires_quoting(self) -> None:
        """Numeric strings should require quoting."""
        assert TOONSpec.requires_quoting("123")
        assert TOONSpec.requires_quoting("-45")
        assert TOONSpec.requires_quoting("3.14")

    def test_list_marker_requires_quoting(self) -> None:
        """List marker prefix should require quoting."""
        assert TOONSpec.requires_quoting("- item")

    def test_array_header_like_requires_quoting(self) -> None:
        """Array header-like strings should require quoting."""
        assert TOONSpec.requires_quoting("[5]:")
        assert TOONSpec.requires_quoting("[0]")


class TestValidateDelimiter:
    """Test delimiter validation."""

    def test_comma_is_valid(self) -> None:
        """Comma should be valid delimiter."""
        TOONSpec.validate_delimiter(",")  # Should not raise

    def test_tab_is_valid(self) -> None:
        """Tab should be valid delimiter."""
        TOONSpec.validate_delimiter("\t")  # Should not raise

    def test_pipe_is_valid(self) -> None:
        """Pipe should be valid delimiter."""
        TOONSpec.validate_delimiter("|")  # Should not raise

    def test_invalid_delimiter_raises_value_error(self) -> None:
        """Invalid delimiter should raise ValueError."""
        with pytest.raises(ValueError, match="delimiter must be"):
            TOONSpec.validate_delimiter(";")

    def test_invalid_delimiter_space(self) -> None:
        """Space should be invalid delimiter."""
        with pytest.raises(ValueError):
            TOONSpec.validate_delimiter(" ")

    def test_invalid_delimiter_empty(self) -> None:
        """Empty string should be invalid delimiter."""
        with pytest.raises(ValueError):
            TOONSpec.validate_delimiter("")


class TestValidateIndent:
    """Test indentation validation."""

    def test_positive_indent_is_valid(self) -> None:
        """Positive indent should be valid."""
        TOONSpec.validate_indent(1)
        TOONSpec.validate_indent(2)
        TOONSpec.validate_indent(4)
        TOONSpec.validate_indent(8)

    def test_zero_indent_raises_value_error(self) -> None:
        """Zero indent should raise ValueError."""
        with pytest.raises(ValueError, match="indent must be positive"):
            TOONSpec.validate_indent(0)

    def test_negative_indent_raises_value_error(self) -> None:
        """Negative indent should raise ValueError."""
        with pytest.raises(ValueError, match="indent must be positive"):
            TOONSpec.validate_indent(-1)

    def test_large_indent_is_valid(self) -> None:
        """Large indent (beyond recommended) should still be valid."""
        TOONSpec.validate_indent(100)  # Valid but not recommended
