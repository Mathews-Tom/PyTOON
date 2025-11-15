"""Unit tests for ArrayEncoder class.

Tests cover all array encoding formats: tabular, inline, and list.
"""

import pytest

from pytoon.encoder.array import ArrayEncoder
from pytoon.utils.errors import TOONEncodeError


class TestArrayEncoderEmpty:
    """Tests for empty array encoding."""

    def test_encode_empty_array(self) -> None:
        """Empty array produces array[0]:"""
        encoder = ArrayEncoder()
        result = encoder.encode([])
        assert result == "array[0]:"

    def test_encode_empty_array_with_indent(self) -> None:
        """Empty array ignores indent parameter."""
        encoder = ArrayEncoder()
        result = encoder.encode([], indent=4)
        assert result == "array[0]:"

    def test_encode_empty_array_with_tab_delimiter(self) -> None:
        """Empty array ignores delimiter parameter."""
        encoder = ArrayEncoder()
        result = encoder.encode([], delimiter="\t")
        assert result == "array[0]:"


class TestArrayEncoderTabular:
    """Tests for tabular format encoding."""

    def test_single_field_single_row(self) -> None:
        """Single element with single field."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}])
        expected = "array[1]{id}:\n  1"
        assert result == expected

    def test_single_field_multiple_rows(self) -> None:
        """Multiple elements with single field."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}, {"id": 2}, {"id": 3}])
        expected = "array[3]{id}:\n  1\n  2\n  3"
        assert result == expected

    def test_multiple_fields_single_row(self) -> None:
        """Single element with multiple fields."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1, "name": "Alice"}])
        # Fields are sorted alphabetically
        expected = "array[1]{id,name}:\n  1,Alice"
        assert result == expected

    def test_multiple_fields_multiple_rows(self) -> None:
        """Multiple elements with multiple fields."""
        encoder = ArrayEncoder()
        result = encoder.encode([
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
        ])
        expected = "array[2]{id,name,role}:\n  1,Alice,admin\n  2,Bob,user"
        assert result == expected

    def test_tabular_with_different_value_types(self) -> None:
        """Tabular format with mixed primitive types."""
        encoder = ArrayEncoder()
        result = encoder.encode([
            {"a": 1, "b": True, "c": "test"},
            {"a": 2, "b": False, "c": "data"},
        ])
        expected = "array[2]{a,b,c}:\n  1,true,test\n  2,false,data"
        assert result == expected

    def test_tabular_with_null_values(self) -> None:
        """Tabular format with None values."""
        encoder = ArrayEncoder()
        result = encoder.encode([
            {"id": 1, "value": None},
            {"id": 2, "value": "set"},
        ])
        expected = "array[2]{id,value}:\n  1,null\n  2,set"
        assert result == expected

    def test_tabular_with_float_values(self) -> None:
        """Tabular format with float values."""
        encoder = ArrayEncoder()
        result = encoder.encode([
            {"x": 1.5, "y": 2.5},
            {"x": 3.14, "y": 0},
        ])
        expected = "array[2]{x,y}:\n  1.5,2.5\n  3.14,0"
        assert result == expected

    def test_tabular_with_custom_indent(self) -> None:
        """Tabular format respects indent parameter."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], indent=4)
        expected = "array[1]{id}:\n    1"
        assert result == expected

    def test_tabular_with_tab_delimiter(self) -> None:
        """Tabular format with tab delimiter includes hint."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"a": 1, "b": 2}], delimiter="\t")
        # Check header includes \t hint and fields use tab delimiter
        assert "array[1\\t]{a\tb}:" in result
        assert "1\t2" in result

    def test_tabular_with_pipe_delimiter(self) -> None:
        """Tabular format with pipe delimiter."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"a": 1, "b": 2}], delimiter="|")
        expected = "array[1]{a|b}:\n  1|2"
        assert result == expected

    def test_tabular_with_quoted_string_values(self) -> None:
        """Strings needing quotes are properly quoted in tabular format."""
        encoder = ArrayEncoder()
        result = encoder.encode([
            {"name": "a,b", "value": "test"},
            {"name": "c,d", "value": "data"},
        ])
        assert '"a,b"' in result
        assert '"c,d"' in result

    def test_tabular_with_empty_string(self) -> None:
        """Empty strings are quoted in tabular format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1, "name": ""}])
        assert '""' in result

    def test_tabular_with_keyword_string(self) -> None:
        """Keyword-like strings are quoted in tabular format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"value": "true"}, {"value": "false"}])
        assert '"true"' in result
        assert '"false"' in result


class TestArrayEncoderInline:
    """Tests for inline format encoding."""

    def test_single_string(self) -> None:
        """Single string element."""
        encoder = ArrayEncoder()
        result = encoder.encode(["a"])
        assert result == "array[1]: a"

    def test_multiple_strings(self) -> None:
        """Multiple string elements."""
        encoder = ArrayEncoder()
        result = encoder.encode(["a", "b", "c"])
        assert result == "array[3]: a,b,c"

    def test_single_integer(self) -> None:
        """Single integer element."""
        encoder = ArrayEncoder()
        result = encoder.encode([42])
        assert result == "array[1]: 42"

    def test_multiple_integers(self) -> None:
        """Multiple integer elements."""
        encoder = ArrayEncoder()
        result = encoder.encode([1, 2, 3, 4, 5])
        assert result == "array[5]: 1,2,3,4,5"

    def test_mixed_primitives(self) -> None:
        """Mixed primitive types (string, int, float, bool, None)."""
        encoder = ArrayEncoder()
        result = encoder.encode(["text", 42, 3.14, True, None])
        assert result == "array[5]: text,42,3.14,true,null"

    def test_all_booleans(self) -> None:
        """Array of booleans."""
        encoder = ArrayEncoder()
        result = encoder.encode([True, False, True])
        assert result == "array[3]: true,false,true"

    def test_all_nulls(self) -> None:
        """Array of None values."""
        encoder = ArrayEncoder()
        result = encoder.encode([None, None, None])
        assert result == "array[3]: null,null,null"

    def test_floats_no_scientific_notation(self) -> None:
        """Floats use decimal notation."""
        encoder = ArrayEncoder()
        result = encoder.encode([1e6, 1e-6])
        assert "1000000" in result
        assert "e" not in result.lower()

    def test_inline_with_quoted_strings(self) -> None:
        """Strings needing quotes are properly quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["hello", "a,b", "world"])
        assert '"a,b"' in result

    def test_inline_with_tab_delimiter(self) -> None:
        """Inline format with tab delimiter."""
        encoder = ArrayEncoder()
        result = encoder.encode(["a", "b", "c"], delimiter="\t")
        assert result == "array[3]: a\tb\tc"

    def test_inline_with_empty_string_element(self) -> None:
        """Empty string element is quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["a", "", "b"])
        assert '""' in result

    def test_inline_negative_numbers(self) -> None:
        """Negative numbers in inline format."""
        encoder = ArrayEncoder()
        result = encoder.encode([-1, -2, -3])
        assert result == "array[3]: -1,-2,-3"


class TestArrayEncoderList:
    """Tests for list format encoding."""

    def test_single_dict_item(self) -> None:
        """Single dict item uses tabular format (uniform dicts)."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"key": "value"}])
        # Single uniform dict uses tabular format
        expected = "array[1]{key}:\n  value"
        assert result == expected

    def test_mixed_dict_and_primitive(self) -> None:
        """Dict and primitive mixed in list."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"k": "v"}, "string", 42])
        expected = "array[3]:\n  - k: v\n  - string\n  - 42"
        assert result == expected

    def test_non_uniform_dicts(self) -> None:
        """Dicts with different keys use list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}, {"name": "Bob"}])
        assert "array[2]:" in result
        assert "- id: 1" in result
        assert "- name: Bob" in result

    def test_dicts_with_nested_array(self) -> None:
        """Dicts containing arrays use list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1, "tags": ["a", "b"]}])
        assert "array[1]:" in result
        assert "- id: 1" in result
        assert "tags:" in result

    def test_dicts_with_nested_dict(self) -> None:
        """Dicts containing nested dicts use list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1, "meta": {"x": 1}}])
        assert "array[1]:" in result

    def test_list_with_custom_indent(self) -> None:
        """List format respects indent parameter."""
        encoder = ArrayEncoder()
        # Use non-uniform dicts to force list format
        result = encoder.encode([{"k": "v"}, {"x": "y"}], indent=4)
        assert "    - k: v" in result

    def test_list_with_quoted_string_values(self) -> None:
        """Strings needing quotes in list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"value": "a,b"}])
        assert '"a,b"' in result

    def test_list_with_boolean_items(self) -> None:
        """Boolean primitives in list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"flag": True}, False])
        assert "true" in result
        assert "false" in result

    def test_list_with_nested_arrays(self) -> None:
        """Nested arrays in list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([[1, 2], [3, 4]])
        assert "array[2]:" in result
        # Should recursively encode nested arrays

    def test_multi_key_dict_in_list(self) -> None:
        """Multi-key uniform dict uses tabular format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"a": 1, "b": 2, "c": 3}])
        # Uniform dicts use tabular format
        assert "array[1]{a,b,c}:" in result
        assert "1,2,3" in result

    def test_multi_key_non_uniform_dict_in_list(self) -> None:
        """Multi-key non-uniform dicts use list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"a": 1, "b": 2}, {"c": 3, "d": 4}])
        assert "array[2]:" in result
        assert "- a: 1" in result
        assert "- c: 3" in result

    def test_empty_dict_in_list(self) -> None:
        """Empty dict in list format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{}])
        assert "- {}" in result


class TestArrayEncoderDepthAndIndentation:
    """Tests for nested depth and indentation."""

    def test_depth_zero_tabular(self) -> None:
        """Tabular format at depth 0."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], current_depth=0)
        assert result.startswith("array[1]{id}:")
        assert "\n  1" in result

    def test_depth_one_tabular(self) -> None:
        """Tabular format at depth 1."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], current_depth=1)
        # Indentation should be 4 spaces (2 * 2)
        assert "\n    1" in result

    def test_depth_two_tabular(self) -> None:
        """Tabular format at depth 2."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], current_depth=2, indent=2)
        # Indentation should be 6 spaces (2 * 3)
        assert "\n      1" in result

    def test_depth_zero_list(self) -> None:
        """List format at depth 0."""
        encoder = ArrayEncoder()
        # Use non-uniform dicts to force list format
        result = encoder.encode([{"k": "v"}, {"x": "y"}], current_depth=0)
        assert "  - k: v" in result

    def test_depth_one_list(self) -> None:
        """List format at depth 1."""
        encoder = ArrayEncoder()
        # Use non-uniform dicts to force list format
        result = encoder.encode([{"k": "v"}, {"x": "y"}], current_depth=1)
        assert "    - k: v" in result

    def test_indent_four_spaces(self) -> None:
        """Custom indent of 4 spaces."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], indent=4)
        assert "\n    1" in result

    def test_indent_single_space(self) -> None:
        """Custom indent of 1 space."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"id": 1}], indent=1)
        assert "\n 1" in result


class TestArrayEncoderEdgeCases:
    """Tests for edge cases and error handling."""

    def test_not_a_list_raises_error(self) -> None:
        """Non-list input raises TOONEncodeError."""
        encoder = ArrayEncoder()
        with pytest.raises(TOONEncodeError, match="Expected list"):
            encoder.encode("not a list")  # type: ignore[arg-type]

    def test_dict_input_raises_error(self) -> None:
        """Dict input raises TOONEncodeError."""
        encoder = ArrayEncoder()
        with pytest.raises(TOONEncodeError, match="Expected list"):
            encoder.encode({"key": "value"})  # type: ignore[arg-type]

    def test_large_array_tabular(self) -> None:
        """Large tabular array encoding."""
        encoder = ArrayEncoder()
        data = [{"id": i, "val": i * 2} for i in range(100)]
        result = encoder.encode(data)
        assert "array[100]{id,val}:" in result
        assert result.count("\n") == 100  # Header + 100 rows

    def test_large_array_inline(self) -> None:
        """Large inline array encoding."""
        encoder = ArrayEncoder()
        data = list(range(100))
        result = encoder.encode(data)
        assert "array[100]:" in result
        assert result.count(",") == 99  # 100 elements, 99 commas

    def test_string_with_newline_quoted(self) -> None:
        """String with newline is quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["line\nbreak"])
        assert '"' in result

    def test_string_with_tab_quoted(self) -> None:
        """String with tab is quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["tab\there"])
        assert '"' in result

    def test_very_long_string(self) -> None:
        """Very long string in array."""
        encoder = ArrayEncoder()
        long_string = "x" * 1000
        result = encoder.encode([long_string])
        assert f"array[1]: {long_string}" == result

    def test_special_float_values(self) -> None:
        """Special float values (NaN, Inf) become null."""
        encoder = ArrayEncoder()
        result = encoder.encode([float("nan"), float("inf"), float("-inf")])
        assert result == "array[3]: null,null,null"

    def test_negative_zero(self) -> None:
        """Negative zero normalized to 0."""
        encoder = ArrayEncoder()
        result = encoder.encode([-0.0])
        assert result == "array[1]: 0"


class TestArrayEncoderTokenEfficiency:
    """Tests for token efficiency validation."""

    def test_tabular_more_efficient_than_json(self) -> None:
        """Tabular format should be more compact than equivalent JSON."""
        encoder = ArrayEncoder()
        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]
        toon_result = encoder.encode(data)
        json_equivalent = (
            '[{"id": 1, "name": "Alice", "email": "alice@example.com"}, '
            '{"id": 2, "name": "Bob", "email": "bob@example.com"}, '
            '{"id": 3, "name": "Charlie", "email": "charlie@example.com"}]'
        )
        # TOON should be shorter
        assert len(toon_result) < len(json_equivalent)

    def test_inline_more_efficient_than_json(self) -> None:
        """Inline format should be more compact than equivalent JSON."""
        encoder = ArrayEncoder()
        data = ["apple", "banana", "cherry", "date", "elderberry"]
        toon_result = encoder.encode(data)
        json_equivalent = '["apple", "banana", "cherry", "date", "elderberry"]'
        # TOON should be shorter (no quotes on safe strings)
        assert len(toon_result) < len(json_equivalent)


class TestArrayEncoderQuotingIntegration:
    """Tests for proper QuotingEngine integration."""

    def test_quoting_keyword_string_in_tabular(self) -> None:
        """Keyword strings quoted in tabular format."""
        encoder = ArrayEncoder()
        result = encoder.encode([{"val": "null"}])
        assert '"null"' in result

    def test_quoting_numeric_string_in_inline(self) -> None:
        """Numeric-looking strings quoted in inline format."""
        encoder = ArrayEncoder()
        result = encoder.encode(["42", "3.14"])
        assert '"42"' in result
        assert '"3.14"' in result

    def test_quoting_string_with_delimiter_in_inline(self) -> None:
        """Strings containing delimiter quoted in inline format."""
        encoder = ArrayEncoder()
        result = encoder.encode(["a,b,c"], delimiter=",")
        assert '"a,b,c"' in result

    def test_quoting_string_with_colon(self) -> None:
        """Strings containing colon are quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["key:value"])
        assert '"key:value"' in result

    def test_quoting_string_with_leading_whitespace(self) -> None:
        """Strings with leading whitespace are quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode([" padded"])
        assert '" padded"' in result

    def test_quoting_list_marker_string(self) -> None:
        """Strings starting with '- ' are quoted."""
        encoder = ArrayEncoder()
        result = encoder.encode(["- item"])
        assert '"- item"' in result
