"""Unit tests for PyToon public API."""

import pytest

from pytoon import (
    TOONDecodeError,
    TOONEncodeError,
    TOONError,
    TOONValidationError,
    __version__,
    __version_info__,
    decode,
    encode,
)


class TestVersionInfo:
    """Test version information exports."""

    def test_version_is_string(self) -> None:
        """__version__ should be a string."""
        assert isinstance(__version__, str)

    def test_version_format(self) -> None:
        """__version__ should be in semver format."""
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_version_info_is_tuple(self) -> None:
        """__version_info__ should be a tuple."""
        assert isinstance(__version_info__, tuple)

    def test_version_info_matches_version(self) -> None:
        """__version_info__ should match __version__."""
        expected = ".".join(str(v) for v in __version_info__)
        assert __version__ == expected


class TestExceptionHierarchy:
    """Test exception hierarchy exports."""

    def test_toon_error_is_base(self) -> None:
        """TOONError should be base exception."""
        assert issubclass(TOONEncodeError, TOONError)
        assert issubclass(TOONDecodeError, TOONError)

    def test_validation_error_is_decode_error(self) -> None:
        """TOONValidationError should be subclass of TOONDecodeError."""
        assert issubclass(TOONValidationError, TOONDecodeError)

    def test_exceptions_are_catchable(self) -> None:
        """All exceptions should be catchable as Exception."""
        assert issubclass(TOONError, Exception)
        assert issubclass(TOONEncodeError, Exception)
        assert issubclass(TOONDecodeError, Exception)
        assert issubclass(TOONValidationError, Exception)


class TestEncodeFunction:
    """Test encode() public API function."""

    def test_encode_simple_dict(self) -> None:
        """encode() should encode simple dicts."""
        result = encode({"name": "Alice"})
        assert "name: Alice" in result

    def test_encode_simple_array(self) -> None:
        """encode() should encode simple arrays."""
        result = encode([1, 2, 3])
        assert "[3]: 1,2,3" in result

    def test_encode_with_custom_indent(self) -> None:
        """encode() should accept indent parameter."""
        result = encode({"key": "value"}, indent=4)
        assert "key: value" in result

    def test_encode_with_custom_delimiter(self) -> None:
        """encode() should accept delimiter parameter."""
        result = encode([1, 2, 3], delimiter="|")
        assert "[3]: 1|2|3" in result

    def test_encode_with_sort_keys(self) -> None:
        """encode() should accept sort_keys parameter."""
        result = encode({"z": 1, "a": 2}, sort_keys=True)
        lines = result.split("\n")
        # With sort_keys, 'a' should come first
        assert lines[0].startswith("a:")

    def test_encode_none(self) -> None:
        """encode() should encode None as 'null'."""
        assert encode(None) == "null"

    def test_encode_bool(self) -> None:
        """encode() should encode booleans."""
        assert encode(True) == "true"
        assert encode(False) == "false"

    def test_encode_integer(self) -> None:
        """encode() should encode integers."""
        assert encode(42) == "42"
        assert encode(-100) == "-100"

    def test_encode_float(self) -> None:
        """encode() should encode floats."""
        assert encode(3.14) == "3.14"

    def test_encode_invalid_type_raises_error(self) -> None:
        """encode() should raise TOONEncodeError for invalid types."""
        with pytest.raises(TOONEncodeError):
            encode({1, 2, 3})  # type: ignore

    def test_encode_invalid_config_raises_value_error(self) -> None:
        """encode() should raise ValueError for invalid config."""
        with pytest.raises(ValueError):
            encode({}, indent=0)


class TestDecodeFunction:
    """Test decode() public API function."""

    def test_decode_simple_object(self) -> None:
        """decode() should decode simple objects."""
        result = decode("name: Alice")
        assert result == {"name": "Alice"}

    def test_decode_simple_array(self) -> None:
        """decode() should decode simple arrays."""
        result = decode("[3]: 1,2,3")
        assert result == [1, 2, 3]

    def test_decode_null(self) -> None:
        """decode() should decode 'null' to None."""
        assert decode("null") is None

    def test_decode_bool(self) -> None:
        """decode() should decode booleans."""
        assert decode("true") is True
        assert decode("false") is False

    def test_decode_integer(self) -> None:
        """decode() should decode integers."""
        assert decode("42") == 42
        assert decode("-100") == -100

    def test_decode_float(self) -> None:
        """decode() should decode floats."""
        assert decode("3.14") == 3.14

    def test_decode_empty_string(self) -> None:
        """decode() should return empty dict for empty string."""
        assert decode("") == {}

    def test_decode_with_strict_mode(self) -> None:
        """decode() should accept strict parameter."""
        # Valid in strict mode
        result = decode("[2]: 1,2", strict=True)
        assert result == [1, 2]

    def test_decode_strict_validates_length(self) -> None:
        """decode() should validate length in strict mode."""
        with pytest.raises(TOONValidationError):
            decode("[3]: 1,2", strict=True)

    def test_decode_lenient_skips_validation(self) -> None:
        """decode() should skip validation in lenient mode."""
        result = decode("[3]: 1,2", strict=False)
        assert result == [1, 2]

    def test_decode_invalid_input_raises_error(self) -> None:
        """decode() should raise TOONDecodeError for invalid input."""
        with pytest.raises(TOONDecodeError):
            decode(123)  # type: ignore

    def test_decode_invalid_config_raises_value_error(self) -> None:
        """decode() should raise ValueError for invalid config."""
        with pytest.raises(ValueError):
            decode("", strict="yes")  # type: ignore


class TestRoundtripFidelity:
    """Test that decode(encode(data)) == data."""

    def test_roundtrip_dict(self) -> None:
        """Dict should roundtrip correctly."""
        data = {"name": "Alice", "age": 30, "active": True}
        assert decode(encode(data)) == data

    def test_roundtrip_array(self) -> None:
        """Array should roundtrip correctly."""
        data = [1, 2, 3, 4, 5]
        assert decode(encode(data)) == data

    def test_roundtrip_tabular(self) -> None:
        """Tabular array should roundtrip correctly."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        assert decode(encode(data)) == data

    def test_roundtrip_none(self) -> None:
        """None should roundtrip correctly."""
        assert decode(encode(None)) is None

    def test_roundtrip_bool(self) -> None:
        """Bool should roundtrip correctly."""
        assert decode(encode(True)) is True
        assert decode(encode(False)) is False

    def test_roundtrip_integer(self) -> None:
        """Integer should roundtrip correctly."""
        assert decode(encode(42)) == 42
        assert decode(encode(-100)) == -100
        assert decode(encode(0)) == 0

    def test_roundtrip_float(self) -> None:
        """Float should roundtrip correctly."""
        assert decode(encode(3.14)) == 3.14
        assert decode(encode(-2.5)) == -2.5

    def test_roundtrip_empty_dict(self) -> None:
        """Empty dict should roundtrip correctly."""
        assert decode(encode({})) == {}

    def test_roundtrip_empty_array(self) -> None:
        """Empty array should roundtrip correctly."""
        assert decode(encode([])) == []

    def test_roundtrip_quoted_string_value(self) -> None:
        """String with special chars should roundtrip."""
        data = {"message": "hello, world"}
        result = decode(encode(data))
        assert result == data


class TestAPIDocstrings:
    """Test that public API has proper documentation."""

    def test_encode_has_docstring(self) -> None:
        """encode() should have a docstring."""
        assert encode.__doc__ is not None
        assert len(encode.__doc__) > 100

    def test_encode_docstring_has_args(self) -> None:
        """encode() docstring should have Args section."""
        assert "Args:" in (encode.__doc__ or "")

    def test_encode_docstring_has_returns(self) -> None:
        """encode() docstring should have Returns section."""
        assert "Returns:" in (encode.__doc__ or "")

    def test_encode_docstring_has_raises(self) -> None:
        """encode() docstring should have Raises section."""
        assert "Raises:" in (encode.__doc__ or "")

    def test_encode_docstring_has_examples(self) -> None:
        """encode() docstring should have Examples section."""
        assert "Examples:" in (encode.__doc__ or "")

    def test_decode_has_docstring(self) -> None:
        """decode() should have a docstring."""
        assert decode.__doc__ is not None
        assert len(decode.__doc__) > 100

    def test_decode_docstring_has_args(self) -> None:
        """decode() docstring should have Args section."""
        assert "Args:" in (decode.__doc__ or "")

    def test_decode_docstring_has_returns(self) -> None:
        """decode() docstring should have Returns section."""
        assert "Returns:" in (decode.__doc__ or "")

    def test_decode_docstring_has_raises(self) -> None:
        """decode() docstring should have Raises section."""
        assert "Raises:" in (decode.__doc__ or "")

    def test_decode_docstring_has_examples(self) -> None:
        """decode() docstring should have Examples section."""
        assert "Examples:" in (decode.__doc__ or "")


class TestPublicAPIExports:
    """Test that all public API members are exported."""

    def test_encode_is_exported(self) -> None:
        """encode should be in pytoon.__all__."""
        import pytoon

        assert "encode" in pytoon.__all__

    def test_decode_is_exported(self) -> None:
        """decode should be in pytoon.__all__."""
        import pytoon

        assert "decode" in pytoon.__all__

    def test_version_is_exported(self) -> None:
        """__version__ should be in pytoon.__all__."""
        import pytoon

        assert "__version__" in pytoon.__all__

    def test_exceptions_are_exported(self) -> None:
        """Exception classes should be in pytoon.__all__."""
        import pytoon

        assert "TOONError" in pytoon.__all__
        assert "TOONEncodeError" in pytoon.__all__
        assert "TOONDecodeError" in pytoon.__all__
        assert "TOONValidationError" in pytoon.__all__
