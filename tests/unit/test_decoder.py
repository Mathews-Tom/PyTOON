"""Unit tests for Decoder class."""

import pytest

from pytoon.core.decoder import Decoder
from pytoon.utils.errors import TOONDecodeError, TOONValidationError


class TestDecoderInit:
    """Test Decoder initialization and configuration."""

    def test_default_configuration(self) -> None:
        """Decoder should initialize with default configuration."""
        decoder = Decoder()
        assert decoder.strict is True
        assert decoder.expand_paths == "off"

    def test_custom_strict_false(self) -> None:
        """Decoder should accept strict=False."""
        decoder = Decoder(strict=False)
        assert decoder.strict is False

    def test_custom_expand_paths_safe(self) -> None:
        """Decoder should accept expand_paths='safe'."""
        decoder = Decoder(expand_paths="safe")
        assert decoder.expand_paths == "safe"

    def test_invalid_strict_type(self) -> None:
        """Decoder should reject non-bool strict."""
        with pytest.raises(ValueError, match="strict must be bool"):
            Decoder(strict="yes")  # type: ignore

    def test_invalid_expand_paths(self) -> None:
        """Decoder should reject invalid expand_paths mode."""
        with pytest.raises(ValueError, match="expand_paths must be"):
            Decoder(expand_paths="invalid")  # type: ignore


class TestDecodePrimitives:
    """Test decoding of primitive values."""

    def test_decode_null(self) -> None:
        """'null' should decode to None."""
        decoder = Decoder()
        assert decoder.decode("null") is None

    def test_decode_true(self) -> None:
        """'true' should decode to True."""
        decoder = Decoder()
        assert decoder.decode("true") is True

    def test_decode_false(self) -> None:
        """'false' should decode to False."""
        decoder = Decoder()
        assert decoder.decode("false") is False

    def test_decode_positive_integer(self) -> None:
        """Positive integers should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("42") == 42
        assert decoder.decode("0") == 0
        assert decoder.decode("1000000") == 1000000

    def test_decode_negative_integer(self) -> None:
        """Negative integers should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("-1") == -1
        assert decoder.decode("-100") == -100

    def test_decode_float(self) -> None:
        """Floats should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("3.14") == 3.14
        assert decoder.decode("0.5") == 0.5

    def test_decode_negative_float(self) -> None:
        """Negative floats should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("-3.14") == -3.14

    def test_decode_quoted_string(self) -> None:
        """Quoted strings should be unquoted."""
        decoder = Decoder()
        assert decoder.decode('"hello"') == "hello"
        assert decoder.decode('"world"') == "world"

    def test_decode_quoted_string_with_escaped_quote(self) -> None:
        """Escaped quotes in strings should be unescaped."""
        decoder = Decoder()
        result = decoder.decode('"he said \\"hi\\""')
        assert result == 'he said "hi"'

    def test_decode_quoted_string_with_escaped_backslash(self) -> None:
        """Escaped backslashes should be unescaped."""
        decoder = Decoder()
        result = decoder.decode('"path\\\\to\\\\file"')
        assert result == "path\\to\\file"

    def test_decode_empty_string_returns_empty_dict(self) -> None:
        """Empty input should return empty dict."""
        decoder = Decoder()
        assert decoder.decode("") == {}

    def test_decode_whitespace_only_returns_empty_dict(self) -> None:
        """Whitespace-only input should return empty dict."""
        decoder = Decoder()
        assert decoder.decode("   ") == {}
        assert decoder.decode("\n\n") == {}

    def test_decode_non_string_raises_error(self) -> None:
        """Non-string input should raise TOONDecodeError."""
        decoder = Decoder()
        with pytest.raises(TOONDecodeError, match="Expected string"):
            decoder.decode(123)  # type: ignore


class TestDecodeArrays:
    """Test decoding of arrays."""

    def test_decode_empty_array(self) -> None:
        """Empty arrays should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("[0]:") == []

    def test_decode_inline_primitive_array(self) -> None:
        """Inline primitive arrays should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("[3]: 1,2,3") == [1, 2, 3]

    def test_decode_inline_array_with_spaces(self) -> None:
        """Inline arrays with spaces should decode correctly."""
        decoder = Decoder()
        assert decoder.decode("[3]: 1, 2, 3") == [1, 2, 3]

    def test_decode_inline_mixed_primitives(self) -> None:
        """Inline arrays with mixed types should decode."""
        decoder = Decoder()
        result = decoder.decode("[4]: 1,hello,true,null")
        assert result == [1, "hello", True, None]

    def test_decode_inline_with_tab_delimiter(self) -> None:
        """Tab-delimited inline arrays should decode."""
        decoder = Decoder()
        result = decoder.decode("[3]: 1\t2\t3")
        assert result == [1, 2, 3]

    def test_decode_inline_with_pipe_delimiter(self) -> None:
        """Pipe-delimited inline arrays should decode."""
        decoder = Decoder()
        result = decoder.decode("[3]: 1|2|3")
        assert result == [1, 2, 3]

    def test_decode_tabular_array(self) -> None:
        """Tabular arrays should decode to list of dicts."""
        decoder = Decoder()
        toon = "[2]{id,name}:\n1,Alice\n2,Bob"
        result = decoder.decode(toon)
        assert result == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    def test_decode_tabular_with_spaces(self) -> None:
        """Tabular arrays with spaces should decode."""
        decoder = Decoder()
        toon = "[2]{id, name}:\n1, Alice\n2, Bob"
        result = decoder.decode(toon)
        assert result == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    def test_decode_list_format_array(self) -> None:
        """List-style arrays should decode correctly."""
        decoder = Decoder()
        toon = "[3]:\n- 1\n- 2\n- 3"
        result = decoder.decode(toon)
        assert result == [1, 2, 3]

    def test_decode_list_format_with_strings(self) -> None:
        """List-style arrays with strings should decode."""
        decoder = Decoder()
        toon = "[2]:\n- hello\n- world"
        result = decoder.decode(toon)
        assert result == ["hello", "world"]

    def test_invalid_array_header_raises_error(self) -> None:
        """Invalid array headers should raise TOONDecodeError."""
        decoder = Decoder()
        with pytest.raises(TOONDecodeError, match="Invalid array header"):
            decoder.decode("[abc]:")

    def test_strict_mode_validates_array_length(self) -> None:
        """Strict mode should validate array length declaration."""
        decoder = Decoder(strict=True)
        with pytest.raises(TOONValidationError, match="declares.*items but found"):
            decoder.decode("[3]: 1,2")  # Declares 3 but has 2

    def test_lenient_mode_skips_length_validation(self) -> None:
        """Lenient mode should not validate array length."""
        decoder = Decoder(strict=False)
        result = decoder.decode("[3]: 1,2")  # Declares 3 but has 2
        assert result == [1, 2]

    def test_strict_mode_validates_tabular_rows(self) -> None:
        """Strict mode should validate tabular row count."""
        decoder = Decoder(strict=True)
        toon = "[3]{id}:\n1\n2"  # Declares 3 but has 2 rows
        with pytest.raises(TOONValidationError, match="declares.*rows but found"):
            decoder.decode(toon)

    def test_strict_mode_validates_field_count(self) -> None:
        """Strict mode should validate field count per row."""
        decoder = Decoder(strict=True)
        toon = "[2]{id,name}:\n1,Alice\n2"  # Second row missing name
        with pytest.raises(TOONValidationError, match="values but expected.*fields"):
            decoder.decode(toon)


class TestDecodeObjects:
    """Test decoding of objects (dictionaries)."""

    def test_decode_simple_object(self) -> None:
        """Simple key-value should decode to dict."""
        decoder = Decoder()
        assert decoder.decode("name: Alice") == {"name": "Alice"}

    def test_decode_multi_key_object(self) -> None:
        """Multi-key objects should decode correctly."""
        decoder = Decoder()
        toon = "name: Alice\nage: 30"
        result = decoder.decode(toon)
        assert result == {"name": "Alice", "age": 30}

    def test_decode_object_with_integer_value(self) -> None:
        """Object with integer value should decode."""
        decoder = Decoder()
        assert decoder.decode("count: 42") == {"count": 42}

    def test_decode_object_with_boolean_value(self) -> None:
        """Object with boolean value should decode."""
        decoder = Decoder()
        assert decoder.decode("active: true") == {"active": True}
        assert decoder.decode("disabled: false") == {"disabled": False}

    def test_decode_object_with_null_value(self) -> None:
        """Object with null value should decode."""
        decoder = Decoder()
        assert decoder.decode("value: null") == {"value": None}

    def test_decode_object_with_float_value(self) -> None:
        """Object with float value should decode."""
        decoder = Decoder()
        assert decoder.decode("price: 3.14") == {"price": 3.14}

    def test_decode_object_with_quoted_string(self) -> None:
        """Object with quoted string should decode."""
        decoder = Decoder()
        result = decoder.decode('message: "hello, world"')
        assert result == {"message": "hello, world"}

    def test_decode_object_underscore_key(self) -> None:
        """Object with underscore in key should decode."""
        decoder = Decoder()
        assert decoder.decode("user_id: 123") == {"user_id": 123}

    def test_decode_object_empty_string_value(self) -> None:
        """Object key with no value should have empty string."""
        decoder = Decoder()
        result = decoder.decode("key:")
        assert result == {"key": ""}


class TestDecodeRoundtrip:
    """Test roundtrip fidelity (decode what encoder produces)."""

    def test_roundtrip_simple_dict(self) -> None:
        """Simple dict should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        data = {"name": "Alice", "age": 30}
        encoded = encoder.encode(data)
        decoded = decoder.decode(encoded)
        assert decoded == data

    def test_roundtrip_primitive_array(self) -> None:
        """Primitive array should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        data = [1, 2, 3, 4, 5]
        encoded = encoder.encode(data)
        decoded = decoder.decode(encoded)
        assert decoded == data

    def test_roundtrip_tabular_array(self) -> None:
        """Tabular array should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        encoded = encoder.encode(data)
        decoded = decoder.decode(encoded)
        assert decoded == data

    def test_roundtrip_none(self) -> None:
        """None should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        assert decoder.decode(encoder.encode(None)) is None

    def test_roundtrip_boolean(self) -> None:
        """Booleans should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        assert decoder.decode(encoder.encode(True)) is True
        assert decoder.decode(encoder.encode(False)) is False

    def test_roundtrip_integer(self) -> None:
        """Integers should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        assert decoder.decode(encoder.encode(42)) == 42
        assert decoder.decode(encoder.encode(-100)) == -100

    def test_roundtrip_float(self) -> None:
        """Floats should roundtrip correctly."""
        from pytoon.core.encoder import Encoder

        encoder = Encoder()
        decoder = Decoder()
        assert decoder.decode(encoder.encode(3.14)) == 3.14
