"""Unit tests for ObjectEncoder class.

Tests cover all object encoding scenarios: empty dicts, flat dicts,
nested dicts, arrays, mixed structures, and edge cases.
"""

import pytest

from pytoon.encoder.object import ObjectEncoder
from pytoon.utils.errors import TOONEncodeError


class TestObjectEncoderEmpty:
    """Tests for empty dictionary encoding."""

    def test_encode_empty_dict(self) -> None:
        """Empty dict returns empty string."""
        encoder = ObjectEncoder()
        result = encoder.encode({})
        assert result == ""

    def test_encode_empty_dict_with_indent(self) -> None:
        """Empty dict ignores indent parameter."""
        encoder = ObjectEncoder()
        result = encoder.encode({}, indent=4)
        assert result == ""

    def test_encode_empty_dict_with_delimiter(self) -> None:
        """Empty dict ignores delimiter parameter."""
        encoder = ObjectEncoder()
        result = encoder.encode({}, delimiter="\t")
        assert result == ""

    def test_encode_empty_dict_with_depth(self) -> None:
        """Empty dict at non-zero depth still returns empty string."""
        encoder = ObjectEncoder()
        result = encoder.encode({}, current_depth=2)
        assert result == ""


class TestObjectEncoderSingleKey:
    """Tests for single key-value pairs."""

    def test_string_value(self) -> None:
        """Single key with string value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"key": "value"})
        assert result == "key: value"

    def test_integer_value(self) -> None:
        """Single key with integer value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"count": 42})
        assert result == "count: 42"

    def test_float_value(self) -> None:
        """Single key with float value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"price": 3.14})
        assert result == "price: 3.14"

    def test_boolean_true_value(self) -> None:
        """Single key with True value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"active": True})
        assert result == "active: true"

    def test_boolean_false_value(self) -> None:
        """Single key with False value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"deleted": False})
        assert result == "deleted: false"

    def test_null_value(self) -> None:
        """Single key with None value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"data": None})
        assert result == "data: null"

    def test_negative_integer(self) -> None:
        """Single key with negative integer."""
        encoder = ObjectEncoder()
        result = encoder.encode({"offset": -100})
        assert result == "offset: -100"

    def test_large_integer(self) -> None:
        """Single key with large integer (no scientific notation)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"bytes": 1000000})
        assert result == "bytes: 1000000"

    def test_zero_value(self) -> None:
        """Single key with zero value."""
        encoder = ObjectEncoder()
        result = encoder.encode({"index": 0})
        assert result == "index: 0"

    def test_empty_string_value(self) -> None:
        """Single key with empty string value (quoted)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"name": ""})
        assert result == 'name: ""'


class TestObjectEncoderMultipleKeys:
    """Tests for multiple key-value pairs."""

    def test_two_string_values(self) -> None:
        """Two keys with string values."""
        encoder = ObjectEncoder()
        result = encoder.encode({"name": "Alice", "city": "NYC"})
        assert result == "name: Alice\ncity: NYC"

    def test_three_mixed_types(self) -> None:
        """Three keys with different value types."""
        encoder = ObjectEncoder()
        result = encoder.encode({"name": "Bob", "age": 30, "active": True})
        assert result == "name: Bob\nage: 30\nactive: true"

    def test_preserves_key_order(self) -> None:
        """Dict key order is preserved (Python 3.7+ guarantee)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"z": 1, "a": 2, "m": 3})
        lines = result.split("\n")
        assert lines[0] == "z: 1"
        assert lines[1] == "a: 2"
        assert lines[2] == "m: 3"

    def test_all_null_values(self) -> None:
        """Multiple keys with all None values."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": None, "b": None, "c": None})
        assert result == "a: null\nb: null\nc: null"

    def test_mixed_boolean_values(self) -> None:
        """Multiple boolean values."""
        encoder = ObjectEncoder()
        result = encoder.encode({"flag1": True, "flag2": False, "flag3": True})
        assert result == "flag1: true\nflag2: false\nflag3: true"

    def test_numeric_values(self) -> None:
        """Multiple numeric values of different types."""
        encoder = ObjectEncoder()
        result = encoder.encode({"int": 10, "float": 2.5, "negative": -5})
        assert result == "int: 10\nfloat: 2.5\nnegative: -5"


class TestObjectEncoderNestedDicts:
    """Tests for nested dictionary structures."""

    def test_single_nested_dict(self) -> None:
        """Single level of nesting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"outer": {"inner": "value"}})
        assert result == "outer:\n  inner: value"

    def test_nested_dict_with_multiple_keys(self) -> None:
        """Nested dict with multiple keys."""
        encoder = ObjectEncoder()
        result = encoder.encode({"user": {"name": "Alice", "age": 30}})
        expected = "user:\n  name: Alice\n  age: 30"
        assert result == expected

    def test_deeply_nested_dict(self) -> None:
        """Three levels of nesting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": {"c": "deep"}}})
        expected = "a:\n  b:\n    c: deep"
        assert result == expected

    def test_very_deeply_nested_dict(self) -> None:
        """Four levels of nesting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"l1": {"l2": {"l3": {"l4": "bottom"}}}})
        expected = "l1:\n  l2:\n    l3:\n      l4: bottom"
        assert result == expected

    def test_nested_empty_dict(self) -> None:
        """Nested empty dict."""
        encoder = ObjectEncoder()
        result = encoder.encode({"container": {}})
        assert result == "container:"

    def test_sibling_nested_dicts(self) -> None:
        """Multiple nested dicts at same level."""
        encoder = ObjectEncoder()
        result = encoder.encode({
            "first": {"a": 1},
            "second": {"b": 2},
        })
        expected = "first:\n  a: 1\nsecond:\n  b: 2"
        assert result == expected

    def test_nested_dict_with_primitives(self) -> None:
        """Nested dict alongside primitive values."""
        encoder = ObjectEncoder()
        result = encoder.encode({
            "name": "Test",
            "config": {"timeout": 30},
            "enabled": True,
        })
        expected = "name: Test\nconfig:\n  timeout: 30\nenabled: true"
        assert result == expected

    def test_nested_dict_custom_indent(self) -> None:
        """Nested dict with custom indent size."""
        encoder = ObjectEncoder()
        result = encoder.encode({"outer": {"inner": "value"}}, indent=4)
        assert result == "outer:\n    inner: value"

    def test_deeply_nested_custom_indent(self) -> None:
        """Deep nesting with 3-space indent."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": {"c": "d"}}}, indent=3)
        assert result == "a:\n   b:\n      c: d"


class TestObjectEncoderArrays:
    """Tests for dictionaries containing arrays."""

    def test_inline_array_value(self) -> None:
        """Dict with inline array of primitives."""
        encoder = ObjectEncoder()
        result = encoder.encode({"items": [1, 2, 3]})
        assert result == "items: array[3]: 1,2,3"

    def test_empty_array_value(self) -> None:
        """Dict with empty array."""
        encoder = ObjectEncoder()
        result = encoder.encode({"list": []})
        assert result == "list: array[0]:"

    def test_string_array_value(self) -> None:
        """Dict with array of strings."""
        encoder = ObjectEncoder()
        result = encoder.encode({"names": ["Alice", "Bob", "Charlie"]})
        assert result == "names: array[3]: Alice,Bob,Charlie"

    def test_tabular_array_value(self) -> None:
        """Dict with tabular array (uniform dicts)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"users": [{"id": 1}, {"id": 2}]})
        # Tabular arrays are displayed on new lines with proper indentation
        expected = "users:\n  [2]{id}:\n  1\n  2"
        assert result == expected

    def test_multiple_arrays(self) -> None:
        """Dict with multiple array values."""
        encoder = ObjectEncoder()
        result = encoder.encode({
            "numbers": [1, 2],
            "strings": ["a", "b"],
        })
        assert "numbers: array[2]: 1,2" in result
        assert "strings: array[2]: a,b" in result

    def test_nested_dict_with_array(self) -> None:
        """Nested dict containing an array."""
        encoder = ObjectEncoder()
        result = encoder.encode({"outer": {"items": [1, 2, 3]}})
        expected = "outer:\n  items: array[3]: 1,2,3"
        assert result == expected


class TestObjectEncoderMixedStructures:
    """Tests for complex mixed structures."""

    def test_mixed_primitives_and_nested(self) -> None:
        """Mix of primitives, nested dicts, and arrays."""
        encoder = ObjectEncoder()
        result = encoder.encode({
            "id": 1,
            "name": "Test",
            "meta": {"created": True},
            "tags": ["a", "b"],
        })
        lines = result.split("\n")
        assert lines[0] == "id: 1"
        assert lines[1] == "name: Test"
        assert lines[2] == "meta:"
        assert lines[3] == "  created: true"
        assert lines[4] == "tags: array[2]: a,b"

    def test_deeply_mixed_structure(self) -> None:
        """Complex nested structure with multiple types."""
        encoder = ObjectEncoder()
        data = {
            "config": {
                "settings": {
                    "timeout": 30,
                    "retry": True,
                },
                "endpoints": ["http://a", "http://b"],
            },
            "version": "1.0",
        }
        result = encoder.encode(data)
        assert "config:" in result
        assert "  settings:" in result
        assert "    timeout: 30" in result
        assert "    retry: true" in result
        assert "  endpoints: array[2]:" in result
        # "1.0" looks like a number so it gets quoted
        assert 'version: "1.0"' in result


class TestObjectEncoderKeyQuoting:
    """Tests for key quoting scenarios."""

    def test_key_with_hyphen(self) -> None:
        """Key containing hyphen requires quoting (not a valid identifier char)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"user-id": 123})
        # Hyphen is not a valid identifier character, so quoting is required
        assert '"user-id": 123' in result

    def test_key_with_space(self) -> None:
        """Key containing space (embedded space, no leading/trailing)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"first name": "Alice"})
        # Space in middle is not leading/trailing whitespace, so no quoting
        assert "first name: Alice" in result

    def test_key_with_colon(self) -> None:
        """Key containing colon needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"time:zone": "UTC"})
        assert '"time:zone": UTC' in result

    def test_key_with_dot(self) -> None:
        """Key containing dot (not a structural char, no quoting needed)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a.b": "value"})
        # Dot is not a structural character, so no quoting
        assert "a.b: value" in result

    def test_numeric_string_key(self) -> None:
        """Key that looks like a number needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"123": "numeric_key"})
        assert '"123": numeric_key' in result

    def test_keyword_key(self) -> None:
        """Key matching reserved keyword needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"true": "keyword_key"})
        assert '"true": keyword_key' in result

    def test_empty_string_key(self) -> None:
        """Empty string key needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"": "empty_key"})
        assert '"": empty_key' in result

    def test_key_with_bracket(self) -> None:
        """Key containing bracket needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"item[0]": "first"})
        assert '"item[0]": first' in result


class TestObjectEncoderValueQuoting:
    """Tests for value quoting scenarios."""

    def test_value_with_delimiter(self) -> None:
        """String value containing delimiter needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"data": "a,b,c"})
        assert 'data: "a,b,c"' in result

    def test_value_with_colon(self) -> None:
        """String value containing colon needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"time": "10:30"})
        assert 'time: "10:30"' in result

    def test_keyword_value(self) -> None:
        """String value matching keyword needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"status": "null"})
        assert 'status: "null"' in result

    def test_numeric_string_value(self) -> None:
        """String value that looks like number needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"code": "123"})
        assert 'code: "123"' in result

    def test_value_with_newline(self) -> None:
        """String value with newline needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"text": "line1\nline2"})
        assert 'text: "line1\\nline2"' in result

    def test_value_with_tab(self) -> None:
        """String value with tab needs quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"text": "col1\tcol2"})
        assert 'text: "col1\\tcol2"' in result

    def test_value_with_quotes(self) -> None:
        """String value containing quotes needs escaping."""
        encoder = ObjectEncoder()
        result = encoder.encode({"quote": 'say "hello"'})
        assert 'quote: "say \\"hello\\""' in result

    def test_value_with_backslash(self) -> None:
        """String value with backslash needs escaping."""
        encoder = ObjectEncoder()
        result = encoder.encode({"path": "C:\\Users"})
        assert 'path: "C:\\\\Users"' in result


class TestObjectEncoderIndentation:
    """Tests for indentation handling."""

    def test_default_indent_is_two(self) -> None:
        """Default indentation is 2 spaces."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": "c"}})
        assert result == "a:\n  b: c"

    def test_indent_four_spaces(self) -> None:
        """4-space indentation."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": "c"}}, indent=4)
        assert result == "a:\n    b: c"

    def test_indent_one_space(self) -> None:
        """1-space indentation."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": "c"}}, indent=1)
        assert result == "a:\n b: c"

    def test_indent_six_spaces(self) -> None:
        """6-space indentation."""
        encoder = ObjectEncoder()
        result = encoder.encode({"a": {"b": "c"}}, indent=6)
        assert result == "a:\n      b: c"

    def test_current_depth_adds_base_indent(self) -> None:
        """Non-zero current_depth adds base indentation."""
        encoder = ObjectEncoder()
        result = encoder.encode({"key": "value"}, current_depth=1)
        assert result == "  key: value"

    def test_current_depth_two(self) -> None:
        """Current depth of 2 adds 4 spaces (2 * 2)."""
        encoder = ObjectEncoder()
        result = encoder.encode({"key": "value"}, current_depth=2)
        assert result == "    key: value"

    def test_nested_with_current_depth(self) -> None:
        """Nested dict with non-zero starting depth."""
        encoder = ObjectEncoder()
        result = encoder.encode({"outer": {"inner": "val"}}, current_depth=1)
        expected = "  outer:\n    inner: val"
        assert result == expected


class TestObjectEncoderDelimiter:
    """Tests for delimiter parameter handling."""

    def test_tab_delimiter_in_array(self) -> None:
        """Tab delimiter passed to nested arrays."""
        encoder = ObjectEncoder()
        result = encoder.encode({"items": [{"a": 1, "b": 2}]}, delimiter="\t")
        assert "\t" in result

    def test_pipe_delimiter_in_array(self) -> None:
        """Pipe delimiter passed to nested arrays."""
        encoder = ObjectEncoder()
        result = encoder.encode({"items": [1, 2]}, delimiter="|")
        assert "1|2" in result

    def test_delimiter_affects_value_quoting(self) -> None:
        """Delimiter affects which strings need quoting."""
        encoder = ObjectEncoder()
        result = encoder.encode({"data": "a|b"}, delimiter="|")
        # | is in the value and delimiter is |, so needs quoting
        assert '"a|b"' in result


class TestObjectEncoderErrors:
    """Tests for error handling."""

    def test_non_dict_input_raises_error(self) -> None:
        """Passing non-dict raises TOONEncodeError."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Expected dict"):
            encoder.encode([1, 2, 3])  # type: ignore[arg-type]

    def test_list_input_raises_error(self) -> None:
        """List input raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Expected dict"):
            encoder.encode(["a", "b"])  # type: ignore[arg-type]

    def test_string_input_raises_error(self) -> None:
        """String input raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Expected dict"):
            encoder.encode("not a dict")  # type: ignore[arg-type]

    def test_none_input_raises_error(self) -> None:
        """None input raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Expected dict"):
            encoder.encode(None)  # type: ignore[arg-type]

    def test_integer_input_raises_error(self) -> None:
        """Integer input raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Expected dict"):
            encoder.encode(42)  # type: ignore[arg-type]

    def test_non_string_key_raises_error(self) -> None:
        """Dict with non-string key raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Dict key must be string"):
            encoder.encode({123: "value"})  # type: ignore[dict-item]

    def test_tuple_key_raises_error(self) -> None:
        """Dict with tuple key raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Dict key must be string"):
            encoder.encode({("a", "b"): "value"})  # type: ignore[dict-item]

    def test_none_key_raises_error(self) -> None:
        """Dict with None key raises error."""
        encoder = ObjectEncoder()
        with pytest.raises(TOONEncodeError, match="Dict key must be string"):
            encoder.encode({None: "value"})  # type: ignore[dict-item]


class TestObjectEncoderSpecialValues:
    """Tests for special value cases."""

    def test_nan_float_becomes_null(self) -> None:
        """NaN float value becomes null."""
        encoder = ObjectEncoder()
        result = encoder.encode({"value": float("nan")})
        assert result == "value: null"

    def test_inf_float_becomes_null(self) -> None:
        """Infinity float value becomes null."""
        encoder = ObjectEncoder()
        result = encoder.encode({"value": float("inf")})
        assert result == "value: null"

    def test_negative_inf_becomes_null(self) -> None:
        """Negative infinity becomes null."""
        encoder = ObjectEncoder()
        result = encoder.encode({"value": float("-inf")})
        assert result == "value: null"

    def test_negative_zero_becomes_zero(self) -> None:
        """Negative zero becomes positive zero."""
        encoder = ObjectEncoder()
        result = encoder.encode({"value": -0.0})
        assert result == "value: 0"

    def test_very_large_float(self) -> None:
        """Very large float without scientific notation."""
        encoder = ObjectEncoder()
        result = encoder.encode({"big": 1e10})
        assert result == "big: 10000000000"

    def test_very_small_float(self) -> None:
        """Very small float precision."""
        encoder = ObjectEncoder()
        result = encoder.encode({"tiny": 0.000001})
        assert "0.000001" in result


class TestObjectEncoderIntegration:
    """Integration tests for complex scenarios."""

    def test_user_profile_structure(self) -> None:
        """Real-world user profile structure."""
        encoder = ObjectEncoder()
        profile = {
            "id": 12345,
            "username": "alice",
            "email": "alice@example.com",
            "active": True,
            "metadata": {
                "created": "2024-01-01",
                "logins": 100,
            },
            "roles": ["admin", "user"],
        }
        result = encoder.encode(profile)
        assert "id: 12345" in result
        assert "username: alice" in result
        assert "email: alice@example.com" in result
        assert "active: true" in result
        assert "metadata:" in result
        assert '  created: "2024-01-01"' in result  # Date strings with hyphens are quoted
        assert "  logins: 100" in result
        assert "roles: array[2]: admin,user" in result

    def test_api_response_structure(self) -> None:
        """API response with nested data."""
        encoder = ObjectEncoder()
        response = {
            "status": "success",
            "code": 200,
            "data": {
                "items": [{"id": 1}, {"id": 2}],
                "total": 2,
            },
            "errors": None,
        }
        result = encoder.encode(response)
        assert "status: success" in result
        assert "code: 200" in result
        assert "data:" in result
        # Tabular arrays are now displayed on new lines with proper indentation
        assert "items:" in result
        assert "[2]{id}:" in result
        assert "total: 2" in result
        assert "errors: null" in result

    def test_config_file_structure(self) -> None:
        """Configuration file structure."""
        encoder = ObjectEncoder()
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "ssl": True,
            },
            "cache": {
                "enabled": False,
                "ttl": 3600,
            },
            "features": ["auth", "logging"],
        }
        result = encoder.encode(config)
        lines = result.split("\n")
        assert "database:" in lines
        assert "cache:" in lines
        assert "features: array[2]: auth,logging" in result
