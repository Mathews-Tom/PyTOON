"""Unit tests for Parser class.

Tests cover:
- Flat object parsing
- Nested object parsing
- Array parsing (tabular, inline, list)
- Type conversion
- Path expansion
- Error handling
"""

import pytest

from pytoon.decoder.lexer import Lexer
from pytoon.decoder.parser import Parser
from pytoon.utils.errors import TOONDecodeError


class TestEmptyInput:
    """Test parsing empty input."""

    def test_empty_string(self) -> None:
        """Test parsing empty string."""
        lexer = Lexer("")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {}

    def test_only_whitespace(self) -> None:
        """Test parsing whitespace only."""
        lexer = Lexer("   \n\n   ")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {}


class TestFlatObjects:
    """Test parsing flat key-value objects."""

    def test_single_key_value(self) -> None:
        """Test single key-value pair."""
        lexer = Lexer("name: Alice")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"name": "Alice"}

    def test_multiple_key_values(self) -> None:
        """Test multiple key-value pairs."""
        lexer = Lexer("name: Alice\nage: 30\ncity: NYC")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"name": "Alice", "age": 30, "city": "NYC"}

    def test_string_value(self) -> None:
        """Test string value parsing."""
        lexer = Lexer('greeting: "Hello World"')
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"greeting": "Hello World"}

    def test_integer_value(self) -> None:
        """Test integer value parsing."""
        lexer = Lexer("count: 42")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"count": 42}
        assert isinstance(result["count"], int)

    def test_float_value(self) -> None:
        """Test float value parsing."""
        lexer = Lexer("price: 19.99")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"price": 19.99}
        assert isinstance(result["price"], float)

    def test_negative_number(self) -> None:
        """Test negative number parsing."""
        lexer = Lexer("offset: -10")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"offset": -10}

    def test_boolean_true(self) -> None:
        """Test boolean true parsing."""
        lexer = Lexer("enabled: true")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"enabled": True}
        assert result["enabled"] is True

    def test_boolean_false(self) -> None:
        """Test boolean false parsing."""
        lexer = Lexer("disabled: false")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"disabled": False}
        assert result["disabled"] is False

    def test_null_value(self) -> None:
        """Test null value parsing."""
        lexer = Lexer("optional: null")
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"optional": None}
        assert result["optional"] is None


class TestNestedObjects:
    """Test parsing nested object structures."""

    def test_simple_nested(self) -> None:
        """Test simple nested object."""
        source = "user:\n  name: Alice\n  age: 30"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_deeply_nested(self) -> None:
        """Test deeply nested object."""
        source = "a:\n  b:\n    c:\n      d: value"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"a": {"b": {"c": {"d": "value"}}}}

    def test_multiple_nested_siblings(self) -> None:
        """Test multiple nested siblings."""
        source = "config:\n  db:\n    host: localhost\n  cache:\n    enabled: true"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        expected = {
            "config": {"db": {"host": "localhost"}, "cache": {"enabled": True}}
        }
        assert result == expected

    def test_mixed_flat_and_nested(self) -> None:
        """Test mixed flat and nested keys."""
        source = "name: App\nconfig:\n  debug: true\nversion: 1"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        expected = {"name": "App", "config": {"debug": True}, "version": 1}
        assert result == expected


class TestPathExpansion:
    """Test dotted key path expansion."""

    def test_dotted_key_expansion(self) -> None:
        """Test that dotted keys are expanded."""
        lexer = Lexer("user.name: Alice")
        parser = Parser(lexer, expand_paths=True)
        result = parser.parse()
        assert result == {"user": {"name": "Alice"}}

    def test_multiple_dotted_keys(self) -> None:
        """Test multiple dotted keys expansion."""
        source = "user.name: Alice\nuser.age: 30"
        lexer = Lexer(source)
        parser = Parser(lexer, expand_paths=True)
        result = parser.parse()
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_no_expansion_when_disabled(self) -> None:
        """Test that expansion can be disabled."""
        lexer = Lexer("user.name: Alice")
        parser = Parser(lexer, expand_paths=False)
        result = parser.parse()
        assert result == {"user.name": "Alice"}

    def test_deeply_dotted_key(self) -> None:
        """Test deeply dotted key expansion."""
        lexer = Lexer("config.db.host.name: localhost")
        parser = Parser(lexer, expand_paths=True)
        result = parser.parse()
        assert result == {"config": {"db": {"host": {"name": "localhost"}}}}


class TestListArrayParsing:
    """Test list-style array parsing."""

    def test_simple_list_array(self) -> None:
        """Test simple list array."""
        source = "items: [3]\n- one\n- two\n- three"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"items": ["one", "two", "three"]}

    def test_list_with_numbers(self) -> None:
        """Test list with numeric values."""
        source = "numbers: [3]\n- 1\n- 2\n- 3"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"numbers": [1, 2, 3]}

    def test_list_with_booleans(self) -> None:
        """Test list with boolean values."""
        source = "flags: [2]\n- true\n- false"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"flags": [True, False]}

    def test_empty_list(self) -> None:
        """Test empty list."""
        source = "empty: [0]"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"empty": []}


class TestTabularArrayParsing:
    """Test tabular array parsing."""

    def test_simple_tabular(self) -> None:
        """Test simple tabular array."""
        source = "users: [2]{id,name}\n1 Alice\n2 Bob"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        expected = {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        }
        assert result == expected

    def test_tabular_with_types(self) -> None:
        """Test tabular with different types."""
        source = "data: [2]{name,active,count}\nAlice true 10\nBob false 20"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        expected = {
            "data": [
                {"name": "Alice", "active": True, "count": 10},
                {"name": "Bob", "active": False, "count": 20},
            ]
        }
        assert result == expected

    def test_single_row_tabular(self) -> None:
        """Test single row tabular array."""
        source = "item: [1]{id,value}\n42 test"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"item": [{"id": 42, "value": "test"}]}

    def test_empty_tabular(self) -> None:
        """Test empty tabular array."""
        source = "empty: [0]{id,name}"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        # Empty tabular should have no rows
        assert "empty" in result
        assert isinstance(result["empty"], list)


class TestTypeConversion:
    """Test type conversion."""

    def test_integer_conversion(self) -> None:
        """Test integer conversion."""
        lexer = Lexer("num: 123")
        parser = Parser(lexer)
        result = parser.parse()
        assert result["num"] == 123
        assert isinstance(result["num"], int)

    def test_float_conversion(self) -> None:
        """Test float conversion."""
        lexer = Lexer("val: 3.14")
        parser = Parser(lexer)
        result = parser.parse()
        assert result["val"] == 3.14
        assert isinstance(result["val"], float)

    def test_large_integer(self) -> None:
        """Test large integer conversion."""
        lexer = Lexer("big: 1234567890")
        parser = Parser(lexer)
        result = parser.parse()
        assert result["big"] == 1234567890

    def test_zero_value(self) -> None:
        """Test zero value."""
        lexer = Lexer("zero: 0")
        parser = Parser(lexer)
        result = parser.parse()
        assert result["zero"] == 0


class TestComplexStructures:
    """Test complex nested structures."""

    def test_object_with_list(self) -> None:
        """Test object containing list."""
        source = "data:\n  items: [2]\n  - first\n  - second"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"data": {"items": ["first", "second"]}}

    def test_multiple_arrays(self) -> None:
        """Test multiple arrays in object."""
        source = "names: [2]\n- Alice\n- Bob\nages: [2]\n- 30\n- 25"
        lexer = Lexer(source)
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"names": ["Alice", "Bob"], "ages": [30, 25]}


class TestErrorHandling:
    """Test error handling."""

    def test_missing_colon(self) -> None:
        """Test error on missing colon."""
        lexer = Lexer("key value")
        parser = Parser(lexer)
        with pytest.raises(TOONDecodeError, match="Expected ':'"):
            parser.parse()

    def test_duplicate_key(self) -> None:
        """Test error on duplicate key."""
        source = "name: Alice\nname: Bob"
        lexer = Lexer(source)
        parser = Parser(lexer)
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            parser.parse()


class TestParserRepr:
    """Test Parser representation."""

    def test_repr(self) -> None:
        """Test parser repr."""
        lexer = Lexer("key: value")
        parser = Parser(lexer)
        r = repr(parser)
        assert "Parser" in r
        assert "pos=" in r
        assert "state=" in r
        assert "expand_paths=" in r


class TestQuotedStrings:
    """Test quoted string handling."""

    def test_quoted_with_spaces(self) -> None:
        """Test quoted string with spaces."""
        lexer = Lexer('msg: "Hello World"')
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"msg": "Hello World"}

    def test_empty_quoted_string(self) -> None:
        """Test empty quoted string."""
        lexer = Lexer('empty: ""')
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"empty": ""}

    def test_quoted_with_escapes(self) -> None:
        """Test quoted string with escapes."""
        lexer = Lexer('text: "line1\\nline2"')
        parser = Parser(lexer)
        result = parser.parse()
        assert result == {"text": "line1\nline2"}
