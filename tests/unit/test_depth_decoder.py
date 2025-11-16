"""Unit tests for depth-based decoder module."""

import pytest

from pytoon.decoder.depth_decoder import (
    decode_toon,
    decode_value_from_cursor,
    decode_object,
    decode_key_value,
    decode_array_from_header,
    decode_inline_array,
    decode_tabular_array,
    decode_list_array,
    decode_list_item,
    decode_object_from_list_item,
)
from pytoon.decoder.scanner import LineCursor, scan_lines
from pytoon.decoder.types import ArrayHeaderInfo
from pytoon.utils.errors import TOONDecodeError, TOONValidationError


class TestDecodeToon:
    """Test decode_toon main entry point."""

    def test_empty_document(self) -> None:
        """Empty document should return empty dict."""
        result = decode_toon("")
        assert result == {}

    def test_whitespace_only_document(self) -> None:
        """Whitespace-only document should return empty dict."""
        result = decode_toon("   \n   ")
        assert result == {}

    def test_single_primitive(self) -> None:
        """Single line without colon should parse as primitive."""
        assert decode_toon("42") == 42
        assert decode_toon("true") is True
        assert decode_toon("null") is None
        assert decode_toon("3.14") == 3.14

    def test_single_quoted_string(self) -> None:
        """Single quoted string should parse correctly."""
        assert decode_toon('"hello world"') == "hello world"

    def test_simple_object(self) -> None:
        """Simple key-value pairs should parse as object."""
        result = decode_toon("name: Alice\nage: 30")
        assert result == {"name": "Alice", "age": 30}

    def test_root_array_header(self) -> None:
        """Root array should parse correctly."""
        result = decode_toon("[2]:\n- 1\n- 2")
        assert result == [1, 2]

    def test_nested_objects_in_list_items(self) -> None:
        """Nested objects in list items should parse correctly."""
        toon = """[2]:
  - id: 1
    meta:
      created: "2025"
  - id: 2
    meta:
      created: "2024"
"""
        result = decode_toon(toon)
        expected = [
            {"id": 1, "meta": {"created": "2025"}},
            {"id": 2, "meta": {"created": "2024"}},
        ]
        assert result == expected

    def test_strict_mode_duplicate_key(self) -> None:
        """Strict mode should raise error on duplicate keys."""
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            decode_toon("key: 1\nkey: 2", strict=True)

    def test_lenient_mode_duplicate_key(self) -> None:
        """Lenient mode should allow duplicate keys (last wins)."""
        result = decode_toon("key: 1\nkey: 2", strict=False)
        assert result == {"key": 2}


class TestDecodeValueFromCursor:
    """Test decode_value_from_cursor function."""

    def test_empty_cursor_raises_error(self) -> None:
        """Empty cursor should raise TOONDecodeError."""
        scan_result = scan_lines("", indent_size=2, strict=True)
        cursor = LineCursor(scan_result.lines, scan_result.blank_lines)
        with pytest.raises(TOONDecodeError, match="No content to decode"):
            decode_value_from_cursor(cursor, indent_size=2, strict=True)


class TestDecodeObject:
    """Test decode_object function."""

    def test_nested_object(self) -> None:
        """Nested object should parse correctly."""
        toon = """parent:
  child: value
"""
        result = decode_toon(toon)
        assert result == {"parent": {"child": "value"}}

    def test_deeply_nested_object(self) -> None:
        """Deeply nested objects should parse correctly."""
        toon = """level1:
  level2:
    level3:
      value: deep
"""
        result = decode_toon(toon)
        assert result == {"level1": {"level2": {"level3": {"value": "deep"}}}}


class TestDecodeKeyValue:
    """Test decode_key_value function."""

    def test_array_header_as_value(self) -> None:
        """Key with array header should parse array correctly."""
        toon = """items[3]:
  - 1
  - 2
  - 3
"""
        result = decode_toon(toon)
        assert result == {"items": [1, 2, 3]}

    def test_inline_array_value(self) -> None:
        """Key with inline array should parse correctly."""
        result = decode_toon("numbers[3]: 1,2,3")
        assert result == {"numbers": [1, 2, 3]}

    def test_tabular_array_value(self) -> None:
        """Key with tabular array should parse correctly."""
        toon = """users[2]{id,name}:
  1,Alice
  2,Bob
"""
        result = decode_toon(toon)
        assert result == {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}


class TestDecodeInlineArray:
    """Test decode_inline_array function."""

    def test_empty_inline_array(self) -> None:
        """Empty inline array should return empty list."""
        result = decode_toon("[0]:")
        assert result == []

    def test_inline_array_with_spaces(self) -> None:
        """Inline array with spaces should parse correctly."""
        result = decode_toon("[3]: 1, 2, 3")
        assert result == [1, 2, 3]

    def test_inline_array_tab_delimiter(self) -> None:
        """Inline array with tab delimiter should auto-detect."""
        result = decode_toon("[3]:\t1\t2\t3")
        assert result == [1, 2, 3]

    def test_inline_array_pipe_delimiter(self) -> None:
        """Inline array with pipe delimiter should auto-detect."""
        result = decode_toon("[3]: 1|2|3")
        assert result == [1, 2, 3]

    def test_inline_array_mixed_types(self) -> None:
        """Inline array with mixed types should parse correctly."""
        result = decode_toon('[4]: 1,true,null,"hello"')
        assert result == [1, True, None, "hello"]

    def test_inline_array_count_mismatch_strict(self) -> None:
        """Strict mode should raise error on count mismatch."""
        with pytest.raises(TOONValidationError, match="Array declares 3 items but found 2"):
            decode_toon("[3]: 1,2", strict=True)

    def test_inline_array_count_mismatch_lenient(self) -> None:
        """Lenient mode should allow count mismatch."""
        result = decode_toon("[3]: 1,2", strict=False)
        assert result == [1, 2]

    def test_empty_inline_array_with_declared_length(self) -> None:
        """Empty inline array with non-zero length should error in strict mode."""
        with pytest.raises(TOONValidationError):
            decode_toon("[2]:  ", strict=True)


class TestDecodeTabularArray:
    """Test decode_tabular_array function."""

    def test_tabular_array_with_quotes(self) -> None:
        """Tabular array with quoted strings should parse correctly."""
        toon = '[2]{name,desc}:\n"Alice","Developer"\n"Bob","Designer"'
        result = decode_toon(toon)
        assert result == [
            {"name": "Alice", "desc": "Developer"},
            {"name": "Bob", "desc": "Designer"},
        ]

    def test_tabular_array_count_mismatch(self) -> None:
        """Strict mode should raise error on row count mismatch."""
        with pytest.raises(TOONValidationError, match="Array declares 3 rows but found 2"):
            decode_toon("[3]{id,name}:\n1,Alice\n2,Bob", strict=True)

    def test_tabular_array_field_count_mismatch(self) -> None:
        """Strict mode should raise error on field count mismatch."""
        with pytest.raises(TOONValidationError, match="Row has 1 values but expected 2 fields"):
            decode_toon("[2]{id,name}:\n1,Alice\n2", strict=True)


class TestDecodeListArray:
    """Test decode_list_array function."""

    def test_list_array_with_objects(self) -> None:
        """List array with object items should parse correctly."""
        toon = """[2]:
- name: Alice
- name: Bob
"""
        result = decode_toon(toon)
        assert result == [{"name": "Alice"}, {"name": "Bob"}]

    def test_list_array_count_mismatch(self) -> None:
        """Strict mode should raise error on count mismatch."""
        with pytest.raises(TOONValidationError, match="Array declares 3 items but found 2"):
            decode_toon("[3]:\n- 1\n- 2", strict=True)

    def test_list_array_empty_items(self) -> None:
        """Empty list items should parse as empty objects."""
        result = decode_toon("[2]:\n-\n-")
        assert result == [{}, {}]


class TestDecodeListItem:
    """Test decode_list_item function."""

    def test_list_item_primitive(self) -> None:
        """List item with primitive should parse correctly."""
        result = decode_toon("[3]:\n- 42\n- true\n- null")
        assert result == [42, True, None]

    def test_list_item_nested_array(self) -> None:
        """List item with nested array should parse correctly."""
        toon = """[2]:
- [2]: 1,2
- [2]: 3,4
"""
        result = decode_toon(toon)
        assert result == [[1, 2], [3, 4]]

    def test_list_item_invalid_format(self) -> None:
        """Invalid list item format should raise error."""
        scan_result = scan_lines("notalist", indent_size=2, strict=True)
        cursor = LineCursor(scan_result.lines, scan_result.blank_lines)
        with pytest.raises(TOONDecodeError, match="Expected list item"):
            decode_list_item(cursor, base_depth=0, indent_size=2, strict=True)


class TestDecodeObjectFromListItem:
    """Test decode_object_from_list_item function."""

    def test_object_with_multiple_fields(self) -> None:
        """Object in list item with multiple fields should parse correctly."""
        toon = """[1]:
  - id: 1
    name: Alice
    active: true
"""
        result = decode_toon(toon)
        assert result == [{"id": 1, "name": "Alice", "active": True}]

    def test_object_with_deeply_nested(self) -> None:
        """Object with deeply nested structure should parse correctly."""
        toon = """[1]:
  - outer:
      middle:
        inner: value
"""
        result = decode_toon(toon)
        assert result == [{"outer": {"middle": {"inner": "value"}}}]

    def test_duplicate_key_in_list_object_strict(self) -> None:
        """Strict mode should raise error on duplicate keys in list object."""
        toon = """[1]:
  - key: 1
    key: 2
"""
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            decode_toon(toon, strict=True)


class TestComplexScenarios:
    """Test complex nested structures."""

    def test_mixed_arrays_in_object(self) -> None:
        """Object with different array types should parse correctly."""
        toon = """inline[3]: 1,2,3
list[2]:
  - a
  - b
tabular[2]{x,y}:
  1,2
  3,4
"""
        result = decode_toon(toon)
        assert result == {
            "inline": [1, 2, 3],
            "list": ["a", "b"],
            "tabular": [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
        }

    def test_objects_in_objects_in_lists(self) -> None:
        """Deeply nested object hierarchies should parse correctly."""
        toon = """items[2]:
  - level1:
      level2:
        value: a
  - level1:
      level2:
        value: b
"""
        result = decode_toon(toon)
        expected = {
            "items": [
                {"level1": {"level2": {"value": "a"}}},
                {"level1": {"level2": {"value": "b"}}},
            ]
        }
        assert result == expected

    def test_blank_lines_ignored(self) -> None:
        """Blank lines should be ignored during parsing."""
        toon = """key1: value1

key2: value2

key3: value3
"""
        result = decode_toon(toon)
        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}
