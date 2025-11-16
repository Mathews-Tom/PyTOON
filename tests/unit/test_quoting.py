"""Unit tests for QuotingEngine class.

Tests cover all quoting rules, escape sequences, and safe identifier checks
as specified in ENCODER-003 acceptance criteria.
"""

import pytest

from pytoon.encoder.quoting import QuotingEngine


class TestNeedsQuoting:
    """Tests for QuotingEngine.needs_quoting() method."""

    def test_empty_string_needs_quoting(self) -> None:
        """Empty string always needs quoting."""
        assert QuotingEngine.needs_quoting("") is True

    def test_true_keyword_needs_quoting(self) -> None:
        """Reserved keyword 'true' needs quoting."""
        assert QuotingEngine.needs_quoting("true") is True

    def test_false_keyword_needs_quoting(self) -> None:
        """Reserved keyword 'false' needs quoting."""
        assert QuotingEngine.needs_quoting("false") is True

    def test_null_keyword_needs_quoting(self) -> None:
        """Reserved keyword 'null' needs quoting."""
        assert QuotingEngine.needs_quoting("null") is True

    def test_keyword_case_sensitive(self) -> None:
        """Keywords are case-sensitive per TOON spec."""
        # Uppercase should NOT match (TOON is case-sensitive)
        assert QuotingEngine.needs_quoting("True") is False
        assert QuotingEngine.needs_quoting("FALSE") is False
        assert QuotingEngine.needs_quoting("NULL") is False

    def test_integer_looks_like_number(self) -> None:
        """Integer strings need quoting."""
        assert QuotingEngine.needs_quoting("42") is True
        assert QuotingEngine.needs_quoting("0") is True
        assert QuotingEngine.needs_quoting("-10") is True
        assert QuotingEngine.needs_quoting("999999") is True

    def test_float_looks_like_number(self) -> None:
        """Float strings need quoting."""
        assert QuotingEngine.needs_quoting("3.14") is True
        assert QuotingEngine.needs_quoting("0.5") is True
        assert QuotingEngine.needs_quoting("-2.71828") is True
        assert QuotingEngine.needs_quoting("100.0") is True

    def test_not_number_with_trailing_chars(self) -> None:
        """Strings starting with digits but not valid numbers need quoting."""
        # These start with digits but aren't valid numbers, causing lexer ambiguity
        assert QuotingEngine.needs_quoting("42px") is True
        assert QuotingEngine.needs_quoting("3.14rad") is True
        assert QuotingEngine.needs_quoting("10%") is True

    def test_contains_comma_delimiter(self) -> None:
        """Strings containing comma delimiter need quoting."""
        assert QuotingEngine.needs_quoting("a,b", ",") is True
        assert QuotingEngine.needs_quoting("one,two,three", ",") is True

    def test_contains_tab_delimiter(self) -> None:
        """Strings containing tab delimiter need quoting."""
        assert QuotingEngine.needs_quoting("a\tb", "\t") is True
        assert QuotingEngine.needs_quoting("col1\tcol2", "\t") is True

    def test_contains_pipe_delimiter(self) -> None:
        """Strings containing pipe delimiter need quoting."""
        assert QuotingEngine.needs_quoting("a|b", "|") is True
        assert QuotingEngine.needs_quoting("left|right", "|") is True

    def test_delimiter_context_aware(self) -> None:
        """Different delimiters give different results."""
        # Comma delimiter, no pipe issue
        assert QuotingEngine.needs_quoting("a|b", ",") is False
        # Pipe delimiter, no comma issue
        assert QuotingEngine.needs_quoting("a,b", "|") is False

    def test_safe_identifier_no_quoting(self) -> None:
        """Safe identifiers do not need quoting."""
        assert QuotingEngine.needs_quoting("hello") is False
        assert QuotingEngine.needs_quoting("user_name") is False
        assert QuotingEngine.needs_quoting("_private") is False
        assert QuotingEngine.needs_quoting("value123") is False
        assert QuotingEngine.needs_quoting("CamelCase") is False

    def test_leading_whitespace_needs_quoting(self) -> None:
        """Strings with leading whitespace need quoting."""
        assert QuotingEngine.needs_quoting(" hello") is True
        assert QuotingEngine.needs_quoting("  indented") is True
        assert QuotingEngine.needs_quoting("\tpadded") is True

    def test_trailing_whitespace_needs_quoting(self) -> None:
        """Strings with trailing whitespace need quoting."""
        assert QuotingEngine.needs_quoting("hello ") is True
        assert QuotingEngine.needs_quoting("value  ") is True

    def test_both_sides_whitespace_needs_quoting(self) -> None:
        """Strings with whitespace on both sides need quoting."""
        assert QuotingEngine.needs_quoting(" padded ") is True
        assert QuotingEngine.needs_quoting("  both  ") is True

    def test_list_marker_needs_quoting(self) -> None:
        """Strings starting with '- ' need quoting."""
        assert QuotingEngine.needs_quoting("- item") is True
        assert QuotingEngine.needs_quoting("- list marker") is True

    def test_not_list_marker_without_space(self) -> None:
        """Dash without space is not a list marker, but hyphens need quoting."""
        # "-item" is not a number (no digit after -) and not "- " marker
        # But it starts with hyphen which can confuse lexer
        assert QuotingEngine.needs_quoting("-item") is False
        # Dash in middle needs quoting to avoid lexer confusion (UUIDs, dates, etc.)
        assert QuotingEngine.needs_quoting("some-thing") is True

    def test_contains_colon_needs_quoting(self) -> None:
        """Strings containing colon need quoting."""
        assert QuotingEngine.needs_quoting("key:value") is True
        assert QuotingEngine.needs_quoting("time:12:30") is True

    def test_contains_brackets_needs_quoting(self) -> None:
        """Strings containing brackets need quoting."""
        assert QuotingEngine.needs_quoting("[5]") is True
        assert QuotingEngine.needs_quoting("array[0]") is True
        assert QuotingEngine.needs_quoting("list]") is True

    def test_contains_braces_needs_quoting(self) -> None:
        """Strings containing braces need quoting."""
        assert QuotingEngine.needs_quoting("{key}") is True
        assert QuotingEngine.needs_quoting("object{") is True
        assert QuotingEngine.needs_quoting("field}") is True

    def test_contains_newline_needs_quoting(self) -> None:
        """Strings containing newlines need quoting."""
        assert QuotingEngine.needs_quoting("line1\nline2") is True
        assert QuotingEngine.needs_quoting("with\nnewline") is True

    def test_contains_carriage_return_needs_quoting(self) -> None:
        """Strings containing carriage returns need quoting."""
        assert QuotingEngine.needs_quoting("line1\rline2") is True
        assert QuotingEngine.needs_quoting("mixed\r\nlines") is True

    def test_contains_backslash_needs_quoting(self) -> None:
        """Strings containing backslash need quoting."""
        assert QuotingEngine.needs_quoting("path\\to\\file") is True
        assert QuotingEngine.needs_quoting("escape\\char") is True

    def test_contains_double_quote_needs_quoting(self) -> None:
        """Strings containing double quote need quoting."""
        assert QuotingEngine.needs_quoting('say "hi"') is True
        assert QuotingEngine.needs_quoting('"quoted"') is True

    def test_complex_safe_string(self) -> None:
        """Complex but safe strings don't need quoting."""
        # These have special chars but not the problematic ones
        assert QuotingEngine.needs_quoting("hello_world") is False
        assert QuotingEngine.needs_quoting("CamelCaseValue") is False
        assert QuotingEngine.needs_quoting("with123numbers") is False

    def test_default_delimiter_is_comma(self) -> None:
        """Default delimiter is comma."""
        # Without specifying delimiter, comma should trigger quoting
        assert QuotingEngine.needs_quoting("a,b") is True


class TestQuoteString:
    """Tests for QuotingEngine.quote_string() method."""

    def test_simple_string(self) -> None:
        """Simple string gets wrapped in quotes."""
        assert QuotingEngine.quote_string("hello") == '"hello"'

    def test_empty_string(self) -> None:
        """Empty string becomes empty quotes."""
        assert QuotingEngine.quote_string("") == '""'

    def test_escape_double_quote(self) -> None:
        """Double quotes are escaped."""
        assert QuotingEngine.quote_string('say "hello"') == '"say \\"hello\\""'
        assert QuotingEngine.quote_string('"quoted"') == '"\\"quoted\\""'

    def test_escape_backslash(self) -> None:
        """Backslashes are escaped."""
        assert QuotingEngine.quote_string("back\\slash") == '"back\\\\slash"'
        assert QuotingEngine.quote_string("\\\\") == '"\\\\\\\\"'

    def test_escape_newline(self) -> None:
        """Newlines are escaped."""
        assert QuotingEngine.quote_string("line1\nline2") == '"line1\\nline2"'

    def test_escape_carriage_return(self) -> None:
        """Carriage returns are escaped."""
        assert QuotingEngine.quote_string("line1\rline2") == '"line1\\rline2"'

    def test_escape_tab(self) -> None:
        """Tabs are escaped."""
        assert QuotingEngine.quote_string("col1\tcol2") == '"col1\\tcol2"'

    def test_multiple_escapes(self) -> None:
        """Multiple escape sequences in one string."""
        result = QuotingEngine.quote_string('a\nb\tc"d\\e')
        assert result == '"a\\nb\\tc\\"d\\\\e"'

    def test_backslash_before_quote(self) -> None:
        """Backslash before quote gets both escaped."""
        # Input: \" (backslash followed by quote)
        # Should become: \\\\" (escaped backslash \\\\ + escaped quote \\")
        result = QuotingEngine.quote_string('\\"')
        assert result == '"\\\\\\""'

    def test_preserve_other_characters(self) -> None:
        """Non-escape characters are preserved."""
        assert QuotingEngine.quote_string("Hello, World!") == '"Hello, World!"'
        assert QuotingEngine.quote_string("{}[]") == '"{}[]"'

    def test_mixed_content(self) -> None:
        """Mixed content with various characters."""
        result = QuotingEngine.quote_string("key: value")
        assert result == '"key: value"'

    def test_keywords_quoted(self) -> None:
        """Keywords are properly quoted."""
        assert QuotingEngine.quote_string("true") == '"true"'
        assert QuotingEngine.quote_string("false") == '"false"'
        assert QuotingEngine.quote_string("null") == '"null"'

    def test_numbers_quoted(self) -> None:
        """Number strings are properly quoted."""
        assert QuotingEngine.quote_string("42") == '"42"'
        assert QuotingEngine.quote_string("3.14") == '"3.14"'


class TestIsSafeIdentifier:
    """Tests for QuotingEngine.is_safe_identifier() method."""

    def test_simple_name(self) -> None:
        """Simple alphabetic names are safe."""
        assert QuotingEngine.is_safe_identifier("name") is True
        assert QuotingEngine.is_safe_identifier("value") is True

    def test_with_underscore(self) -> None:
        """Names with underscores are safe."""
        assert QuotingEngine.is_safe_identifier("user_id") is True
        assert QuotingEngine.is_safe_identifier("first_name") is True

    def test_starts_with_underscore(self) -> None:
        """Names starting with underscore are safe."""
        assert QuotingEngine.is_safe_identifier("_private") is True
        assert QuotingEngine.is_safe_identifier("__dunder__") is True

    def test_with_numbers(self) -> None:
        """Names with numbers (not at start) are safe."""
        assert QuotingEngine.is_safe_identifier("item2") is True
        assert QuotingEngine.is_safe_identifier("value123") is True

    def test_starts_with_number_not_safe(self) -> None:
        """Names starting with number are not safe."""
        assert QuotingEngine.is_safe_identifier("123key") is False
        assert QuotingEngine.is_safe_identifier("2value") is False

    def test_with_dash_not_safe(self) -> None:
        """Names with dashes are not safe."""
        assert QuotingEngine.is_safe_identifier("key-name") is False
        assert QuotingEngine.is_safe_identifier("some-value") is False

    def test_with_dot_not_safe(self) -> None:
        """Names with dots are not safe."""
        assert QuotingEngine.is_safe_identifier("key.name") is False
        assert QuotingEngine.is_safe_identifier("nested.path") is False

    def test_with_space_not_safe(self) -> None:
        """Names with spaces are not safe."""
        assert QuotingEngine.is_safe_identifier("key name") is False
        assert QuotingEngine.is_safe_identifier("some value") is False

    def test_empty_string_not_safe(self) -> None:
        """Empty string is not a safe identifier."""
        assert QuotingEngine.is_safe_identifier("") is False

    def test_special_characters_not_safe(self) -> None:
        """Names with special characters are not safe."""
        assert QuotingEngine.is_safe_identifier("key@name") is False
        assert QuotingEngine.is_safe_identifier("value!") is False
        assert QuotingEngine.is_safe_identifier("has:colon") is False

    def test_uppercase(self) -> None:
        """Uppercase names are safe."""
        assert QuotingEngine.is_safe_identifier("NAME") is True
        assert QuotingEngine.is_safe_identifier("VALUE") is True

    def test_mixed_case(self) -> None:
        """Mixed case names are safe."""
        assert QuotingEngine.is_safe_identifier("CamelCase") is True
        assert QuotingEngine.is_safe_identifier("mixedCASE") is True


class TestIntegration:
    """Integration tests for QuotingEngine methods working together."""

    def test_needs_quoting_then_quote(self) -> None:
        """If needs_quoting returns True, quote_string should be used."""
        test_cases = [
            "",
            "true",
            "false",
            "null",
            "42",
            "3.14",
            "a,b",
            " padded",
            "- item",
            "line\nbreak",
            'has"quote',
        ]
        for value in test_cases:
            assert QuotingEngine.needs_quoting(value) is True
            quoted = QuotingEngine.quote_string(value)
            assert quoted.startswith('"')
            assert quoted.endswith('"')

    def test_safe_identifier_no_quoting_needed(self) -> None:
        """Safe identifiers should not need quoting."""
        safe_ids = ["name", "user_id", "_private", "value123"]
        for identifier in safe_ids:
            assert QuotingEngine.is_safe_identifier(identifier) is True
            assert QuotingEngine.needs_quoting(identifier) is False

    def test_unsafe_identifier_may_need_quoting(self) -> None:
        """Unsafe identifiers may or may not need quoting."""
        # This has dot, not safe identifier but doesn't need quoting
        assert QuotingEngine.is_safe_identifier("key.name") is False
        assert QuotingEngine.needs_quoting("key.name") is False  # No structural chars

        # This has dash, not safe identifier and needs quoting (lexer ambiguity)
        assert QuotingEngine.is_safe_identifier("some-thing") is False
        assert QuotingEngine.needs_quoting("some-thing") is True  # Hyphens cause lexer issues


class TestEdgeCases:
    """Edge case tests for QuotingEngine."""

    def test_single_character(self) -> None:
        """Single character strings."""
        assert QuotingEngine.needs_quoting("a") is False
        assert QuotingEngine.needs_quoting("_") is False
        assert QuotingEngine.needs_quoting(",") is True
        assert QuotingEngine.needs_quoting(":") is True
        assert QuotingEngine.needs_quoting(" ") is True

    def test_very_long_string(self) -> None:
        """Very long strings are handled."""
        long_safe = "a" * 10000
        assert QuotingEngine.needs_quoting(long_safe) is False

        long_with_comma = "a" * 5000 + "," + "b" * 5000
        assert QuotingEngine.needs_quoting(long_with_comma) is True

    def test_unicode_characters(self) -> None:
        """Unicode characters in strings."""
        # Unicode letters don't need quoting unless they contain structural chars
        assert QuotingEngine.needs_quoting("hello") is False
        assert QuotingEngine.needs_quoting("caf\u00e9") is False  # cafe with accent
        assert QuotingEngine.needs_quoting("\u4e2d\u6587") is False  # Chinese chars
        # But emoji might have issues - test specific cases
        assert QuotingEngine.needs_quoting("price:\u0024100") is True  # has colon

    def test_only_whitespace(self) -> None:
        """Strings with only whitespace."""
        assert QuotingEngine.needs_quoting("   ") is True  # leading/trailing space
        assert QuotingEngine.needs_quoting("\t\t") is True  # contains tab

    def test_multiple_same_delimiters(self) -> None:
        """Multiple instances of the delimiter."""
        assert QuotingEngine.needs_quoting("a,b,c,d", ",") is True
        assert QuotingEngine.needs_quoting("col1\tcol2\tcol3", "\t") is True

    def test_negative_float_looks_like_number(self) -> None:
        """Negative floats need quoting."""
        assert QuotingEngine.needs_quoting("-0.5") is True
        assert QuotingEngine.needs_quoting("-123.456") is True

    def test_scientific_notation_not_matched(self) -> None:
        """Scientific notation is not matched as number pattern, but starts with digit."""
        # TOON doesn't use scientific notation, so "1e6" isn't our number pattern
        # BUT it starts with a digit, so it needs quoting to avoid lexer ambiguity
        assert QuotingEngine.needs_quoting("1e6") is True  # Starts with digit
        assert QuotingEngine.needs_quoting("2.5e-3") is True  # Contains hyphen

    def test_leading_zeros(self) -> None:
        """Numbers with leading zeros need quoting."""
        # Our pattern matches "0" but not "00" or "007"
        # But they start with digits, so need quoting for lexer safety
        assert QuotingEngine.needs_quoting("0") is True
        assert QuotingEngine.needs_quoting("00") is True  # Starts with digit
        assert QuotingEngine.needs_quoting("007") is True  # Starts with digit

    def test_decimal_without_whole_part(self) -> None:
        """Decimal without whole number part."""
        # ".5" is not matched by our pattern (requires digit before decimal)
        assert QuotingEngine.needs_quoting(".5") is False  # Not a valid number pattern


class TestDelimiterVariations:
    """Tests for different delimiter configurations."""

    def test_comma_delimiter_default(self) -> None:
        """Comma is the default delimiter."""
        assert QuotingEngine.needs_quoting("value") is False
        assert QuotingEngine.needs_quoting("a,b") is True

    def test_tab_delimiter(self) -> None:
        """Tab delimiter context."""
        # Tab in value needs quoting with tab delimiter
        assert QuotingEngine.needs_quoting("col1\tcol2", "\t") is True
        # Comma doesn't need quoting with tab delimiter
        assert QuotingEngine.needs_quoting("a,b", "\t") is False

    def test_pipe_delimiter(self) -> None:
        """Pipe delimiter context."""
        # Pipe in value needs quoting with pipe delimiter
        assert QuotingEngine.needs_quoting("left|right", "|") is True
        # Comma doesn't need quoting with pipe delimiter
        assert QuotingEngine.needs_quoting("a,b", "|") is False
        # Tab doesn't need quoting with pipe delimiter (unless it has the char)
        assert QuotingEngine.needs_quoting("a\tb", "|") is True  # tab is special char
