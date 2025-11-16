"""Unit tests for Encoder class."""

import pytest

from pytoon.core.encoder import Encoder
from pytoon.utils.errors import TOONEncodeError


class TestEncoderInit:
    """Test Encoder initialization and configuration."""

    def test_default_configuration(self) -> None:
        """Encoder should initialize with default configuration."""
        encoder = Encoder()
        assert encoder.indent == 2
        assert encoder.delimiter == ","
        assert encoder.key_folding == "off"
        assert encoder.ensure_ascii is False
        assert encoder.sort_keys is False

    def test_custom_indent(self) -> None:
        """Encoder should accept custom indent."""
        encoder = Encoder(indent=4)
        assert encoder.indent == 4

    def test_custom_delimiter_tab(self) -> None:
        """Encoder should accept tab delimiter."""
        encoder = Encoder(delimiter="\t")
        assert encoder.delimiter == "\t"

    def test_custom_delimiter_pipe(self) -> None:
        """Encoder should accept pipe delimiter."""
        encoder = Encoder(delimiter="|")
        assert encoder.delimiter == "|"

    def test_custom_key_folding(self) -> None:
        """Encoder should accept safe key folding mode."""
        encoder = Encoder(key_folding="safe")
        assert encoder.key_folding == "safe"

    def test_ensure_ascii_true(self) -> None:
        """Encoder should accept ensure_ascii=True."""
        encoder = Encoder(ensure_ascii=True)
        assert encoder.ensure_ascii is True

    def test_sort_keys_true(self) -> None:
        """Encoder should accept sort_keys=True."""
        encoder = Encoder(sort_keys=True)
        assert encoder.sort_keys is True

    def test_invalid_indent_zero(self) -> None:
        """Encoder should reject zero indent."""
        with pytest.raises(ValueError, match="indent must be positive"):
            Encoder(indent=0)

    def test_invalid_indent_negative(self) -> None:
        """Encoder should reject negative indent."""
        with pytest.raises(ValueError, match="indent must be positive"):
            Encoder(indent=-1)

    def test_invalid_delimiter(self) -> None:
        """Encoder should reject invalid delimiter."""
        with pytest.raises(ValueError, match="delimiter must be"):
            Encoder(delimiter=";")  # type: ignore

    def test_invalid_key_folding(self) -> None:
        """Encoder should reject invalid key_folding mode."""
        with pytest.raises(ValueError, match="key_folding must be"):
            Encoder(key_folding="invalid")  # type: ignore


class TestEncodePrimitives:
    """Test encoding of primitive values."""

    def test_encode_none(self) -> None:
        """None should encode to 'null'."""
        encoder = Encoder()
        assert encoder.encode(None) == "null"

    def test_encode_true(self) -> None:
        """True should encode to 'true'."""
        encoder = Encoder()
        assert encoder.encode(True) == "true"

    def test_encode_false(self) -> None:
        """False should encode to 'false'."""
        encoder = Encoder()
        assert encoder.encode(False) == "false"

    def test_encode_positive_integer(self) -> None:
        """Positive integers should encode as strings."""
        encoder = Encoder()
        assert encoder.encode(42) == "42"
        assert encoder.encode(0) == "0"
        assert encoder.encode(1000000) == "1000000"

    def test_encode_negative_integer(self) -> None:
        """Negative integers should encode with minus sign."""
        encoder = Encoder()
        assert encoder.encode(-1) == "-1"
        assert encoder.encode(-100) == "-100"

    def test_encode_float(self) -> None:
        """Floats should encode without scientific notation."""
        encoder = Encoder()
        assert encoder.encode(3.14) == "3.14"
        assert encoder.encode(0.5) == "0.5"

    def test_encode_float_strips_trailing_zeros(self) -> None:
        """Floats should strip unnecessary trailing zeros."""
        encoder = Encoder()
        assert encoder.encode(3.0) == "3"
        assert encoder.encode(10.0) == "10"

    def test_encode_negative_zero(self) -> None:
        """Negative zero should normalize to zero."""
        encoder = Encoder()
        assert encoder.encode(-0.0) == "0"

    def test_encode_nan(self) -> None:
        """NaN should encode to 'null'."""
        encoder = Encoder()
        assert encoder.encode(float("nan")) == "null"

    def test_encode_positive_infinity(self) -> None:
        """Positive infinity should encode to 'null'."""
        encoder = Encoder()
        assert encoder.encode(float("inf")) == "null"

    def test_encode_negative_infinity(self) -> None:
        """Negative infinity should encode to 'null'."""
        encoder = Encoder()
        assert encoder.encode(float("-inf")) == "null"

    def test_encode_simple_string(self) -> None:
        """Simple strings should encode without quotes."""
        encoder = Encoder()
        assert encoder.encode("hello") == "hello"
        assert encoder.encode("world") == "world"

    def test_encode_string_with_special_chars(self) -> None:
        """Strings with special characters should be quoted."""
        encoder = Encoder()
        assert encoder.encode("hello, world") == '"hello, world"'
        assert encoder.encode("key:value") == '"key:value"'

    def test_encode_empty_string(self) -> None:
        """Empty strings should be quoted."""
        encoder = Encoder()
        assert encoder.encode("") == '""'

    def test_encode_string_with_quotes(self) -> None:
        """Strings with quotes should escape them."""
        encoder = Encoder()
        result = encoder.encode('he said "hi"')
        assert '\\"' in result

    def test_encode_string_with_backslash(self) -> None:
        """Strings with backslashes should escape them."""
        encoder = Encoder()
        result = encoder.encode("path\\to\\file")
        assert "\\\\" in result

    def test_encode_boolean_like_string(self) -> None:
        """Boolean-like strings should be quoted."""
        encoder = Encoder()
        assert encoder.encode("true") == '"true"'
        assert encoder.encode("false") == '"false"'

    def test_encode_null_like_string(self) -> None:
        """Null-like strings should be quoted."""
        encoder = Encoder()
        assert encoder.encode("null") == '"null"'

    def test_encode_numeric_like_string(self) -> None:
        """Numeric-like strings should be quoted."""
        encoder = Encoder()
        assert encoder.encode("123") == '"123"'
        assert encoder.encode("-45") == '"-45"'


class TestEncodeArrays:
    """Test encoding of arrays."""

    def test_encode_empty_array(self) -> None:
        """Empty arrays should encode with length 0."""
        encoder = Encoder()
        assert encoder.encode([]) == "[0]:"

    def test_encode_inline_primitive_array(self) -> None:
        """Arrays of primitives should encode inline."""
        encoder = Encoder()
        result = encoder.encode([1, 2, 3])
        assert result == "[3]: 1,2,3"

    def test_encode_inline_with_custom_delimiter(self) -> None:
        """Inline arrays should respect custom delimiter."""
        encoder = Encoder(delimiter="|")
        result = encoder.encode([1, 2, 3])
        assert result == "[3]: 1|2|3"

    def test_encode_inline_mixed_primitives(self) -> None:
        """Arrays with mixed primitives should encode inline."""
        encoder = Encoder()
        result = encoder.encode([1, "hello", True, None])
        assert "[4]:" in result
        assert "1" in result
        assert "hello" in result
        assert "true" in result
        assert "null" in result

    def test_encode_tabular_array(self) -> None:
        """Arrays of uniform dicts should encode as tabular."""
        encoder = Encoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = encoder.encode(data)
        assert "[2]{" in result
        assert "id" in result
        assert "name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_encode_tabular_respects_sort_keys(self) -> None:
        """Tabular arrays should sort keys when sort_keys=True."""
        encoder = Encoder(sort_keys=True)
        data = [{"z": 1, "a": 2}]
        result = encoder.encode(data)
        # With sort_keys, 'a' should come before 'z'
        assert result.index("a") < result.index("z")

    def test_encode_list_format_for_nested_arrays(self) -> None:
        """Arrays with nested structures should use list format."""
        encoder = Encoder()
        data = [[1, 2], [3, 4]]
        result = encoder.encode(data)
        assert "[2]:" in result
        assert "- " in result

    def test_encode_list_format_for_non_uniform_dicts(self) -> None:
        """Arrays with non-uniform dicts should use list format."""
        encoder = Encoder()
        data = [{"a": 1}, {"b": 2}]
        result = encoder.encode(data)
        assert "[2]:" in result
        assert "- " in result


class TestEncodeObjects:
    """Test encoding of objects (dictionaries)."""

    def test_encode_empty_dict(self) -> None:
        """Empty dicts should encode to empty string."""
        encoder = Encoder()
        assert encoder.encode({}) == ""

    def test_encode_simple_dict(self) -> None:
        """Simple dicts should encode as key: value pairs."""
        encoder = Encoder()
        result = encoder.encode({"name": "Alice"})
        assert "name: Alice" in result

    def test_encode_multi_key_dict(self) -> None:
        """Multi-key dicts should have each key on its line."""
        encoder = Encoder()
        result = encoder.encode({"name": "Alice", "age": 30})
        assert "name: Alice" in result
        assert "age: 30" in result

    def test_encode_sorted_keys(self) -> None:
        """Dict keys should be sorted when sort_keys=True."""
        encoder = Encoder(sort_keys=True)
        result = encoder.encode({"z": 1, "a": 2, "m": 3})
        lines = result.split("\n")
        assert lines[0].startswith("a:")
        assert lines[1].startswith("m:")
        assert lines[2].startswith("z:")

    def test_encode_nested_dict(self) -> None:
        """Nested dicts should be indented properly."""
        encoder = Encoder(indent=2)
        data = {"outer": {"inner": "value"}}
        result = encoder.encode(data)
        assert "outer:" in result
        assert "inner: value" in result

    def test_encode_dict_with_array_value(self) -> None:
        """Dicts with array values should encode arrays inline."""
        encoder = Encoder()
        data = {"items": [1, 2, 3]}
        result = encoder.encode(data)
        assert "items:" in result
        assert "[3]:" in result

    def test_encode_non_string_key_raises_error(self) -> None:
        """Non-string keys should raise TOONEncodeError."""
        encoder = Encoder()
        with pytest.raises(TOONEncodeError, match="keys must be strings"):
            encoder.encode({123: "value"})  # type: ignore


class TestEncodeDepthLimits:
    """Test encoding depth limits."""

    def test_max_nesting_depth_exceeded(self) -> None:
        """Exceeding max nesting depth should raise error."""
        encoder = Encoder()
        # Create deeply nested structure
        data: dict[str, object] = {"level": {}}
        current = data["level"]
        for _ in range(105):  # Exceed 100 levels
            assert isinstance(current, dict)
            current["nested"] = {}  # type: ignore[index]
            current = current["nested"]  # type: ignore[index]
        with pytest.raises(TOONEncodeError, match="Maximum nesting depth"):
            encoder.encode(data)


class TestEncodeUnsupportedTypes:
    """Test handling of unsupported types."""

    def test_encode_set_uses_type_registry(self) -> None:
        """Sets are now supported via TypeRegistry."""
        encoder = Encoder()
        # Set is now supported via TypeRegistry
        result = encoder.encode({1, 2, 3})  # type: ignore
        assert "set:" in result

    def test_encode_tuple_raises_error(self) -> None:
        """Tuples should raise TOONEncodeError."""
        encoder = Encoder()
        with pytest.raises(TOONEncodeError, match="Cannot encode type"):
            encoder.encode((1, 2, 3))  # type: ignore

    def test_encode_custom_object_raises_error(self) -> None:
        """Custom objects should raise TOONEncodeError."""

        class CustomObj:
            pass

        encoder = Encoder()
        with pytest.raises(TOONEncodeError, match="Cannot encode type"):
            encoder.encode(CustomObj())  # type: ignore
