"""Comprehensive unit tests for ValueEncoder.

This module contains 100+ test cases covering all edge cases and
acceptance criteria for the ValueEncoder class.
"""

import math
import pytest

from pytoon.encoder.value import ValueEncoder
from pytoon.utils.errors import TOONEncodeError


class TestValueEncoderNone:
    """Tests for None encoding."""

    def test_encode_none(self) -> None:
        """None encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(None) == "null"

    def test_encode_none_type_check(self) -> None:
        """None encoding returns string."""
        encoder = ValueEncoder()
        result = encoder.encode_value(None)
        assert isinstance(result, str)

    def test_encode_none_exact_match(self) -> None:
        """None encoding is exactly 'null', not 'None'."""
        encoder = ValueEncoder()
        result = encoder.encode_value(None)
        assert result != "None"
        assert result == "null"


class TestValueEncoderBooleans:
    """Tests for boolean encoding."""

    def test_encode_true(self) -> None:
        """True encodes to lowercase 'true'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(True) == "true"

    def test_encode_false(self) -> None:
        """False encodes to lowercase 'false'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(False) == "false"

    def test_encode_true_lowercase(self) -> None:
        """True encoding is lowercase, not 'True'."""
        encoder = ValueEncoder()
        result = encoder.encode_value(True)
        assert result != "True"
        assert result.islower()

    def test_encode_false_lowercase(self) -> None:
        """False encoding is lowercase, not 'False'."""
        encoder = ValueEncoder()
        result = encoder.encode_value(False)
        assert result != "False"
        assert result.islower()

    def test_encode_bool_not_integer(self) -> None:
        """Boolean True is not encoded as '1'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(True) != "1"
        assert encoder.encode_value(False) != "0"

    def test_encode_bool_type_priority(self) -> None:
        """Boolean check comes before integer check."""
        encoder = ValueEncoder()
        assert encoder.encode_value(True) == "true"
        assert encoder.encode_value(False) == "false"

    def test_encode_bool_returns_string(self) -> None:
        """Boolean encoding returns string type."""
        encoder = ValueEncoder()
        assert isinstance(encoder.encode_value(True), str)
        assert isinstance(encoder.encode_value(False), str)


class TestValueEncoderIntegers:
    """Tests for integer encoding."""

    def test_encode_zero(self) -> None:
        """Zero encodes to '0'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(0) == "0"

    def test_encode_positive_int(self) -> None:
        """Positive integer encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(42) == "42"

    def test_encode_negative_int(self) -> None:
        """Negative integer encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-42) == "-42"

    def test_encode_one(self) -> None:
        """One encodes to '1'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(1) == "1"

    def test_encode_negative_one(self) -> None:
        """Negative one encodes to '-1'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-1) == "-1"

    def test_encode_large_integer(self) -> None:
        """Large integer encodes without scientific notation."""
        encoder = ValueEncoder()
        assert encoder.encode_value(1000000) == "1000000"

    def test_encode_very_large_integer(self) -> None:
        """Very large integer encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(999999999999) == "999999999999"

    def test_encode_negative_large_integer(self) -> None:
        """Large negative integer encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-1000000) == "-1000000"

    def test_encode_max_int(self) -> None:
        """Maximum representable integer encodes correctly."""
        encoder = ValueEncoder()
        big_int = 10**20
        result = encoder.encode_value(big_int)
        assert result == str(big_int)

    def test_encode_min_int(self) -> None:
        """Minimum representable integer encodes correctly."""
        encoder = ValueEncoder()
        small_int = -(10**20)
        result = encoder.encode_value(small_int)
        assert result == str(small_int)

    def test_encode_integer_no_decimal(self) -> None:
        """Integer encoding has no decimal point."""
        encoder = ValueEncoder()
        result = encoder.encode_value(100)
        assert "." not in result

    def test_encode_integer_returns_string(self) -> None:
        """Integer encoding returns string type."""
        encoder = ValueEncoder()
        assert isinstance(encoder.encode_value(42), str)


class TestValueEncoderFloats:
    """Tests for float encoding."""

    def test_encode_float_positive(self) -> None:
        """Positive float encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(3.14) == "3.14"

    def test_encode_float_negative(self) -> None:
        """Negative float encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-3.14) == "-3.14"

    def test_encode_float_zero(self) -> None:
        """Float zero encodes to '0'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(0.0) == "0"

    def test_encode_negative_zero(self) -> None:
        """Negative zero encodes to '0' (normalized)."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-0.0) == "0"

    def test_encode_float_one(self) -> None:
        """Float 1.0 encodes to '1'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(1.0) == "1"

    def test_encode_float_half(self) -> None:
        """Float 0.5 encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(0.5) == "0.5"

    def test_encode_float_scientific_notation_large(self) -> None:
        """Large float in scientific notation encodes without exponent."""
        encoder = ValueEncoder()
        assert encoder.encode_value(1e6) == "1000000"

    def test_encode_float_scientific_notation_small(self) -> None:
        """Small float encodes without scientific notation."""
        encoder = ValueEncoder()
        result = encoder.encode_value(1e-5)
        assert "e" not in result.lower()
        assert result == "0.00001"

    def test_encode_float_very_large(self) -> None:
        """Very large float encodes without scientific notation."""
        encoder = ValueEncoder()
        result = encoder.encode_value(1e10)
        assert "e" not in result.lower()
        assert result == "10000000000"

    def test_encode_float_trailing_zeros_removed(self) -> None:
        """Trailing zeros are removed from float."""
        encoder = ValueEncoder()
        assert encoder.encode_value(3.10) == "3.1"

    def test_encode_float_trailing_decimal_removed(self) -> None:
        """Trailing decimal point is removed."""
        encoder = ValueEncoder()
        result = encoder.encode_value(3.0)
        assert not result.endswith(".")
        assert result == "3"

    def test_encode_float_precision(self) -> None:
        """Float maintains reasonable precision."""
        encoder = ValueEncoder()
        result = encoder.encode_value(0.1 + 0.2)
        assert "0.3" in result

    def test_encode_float_small_decimal(self) -> None:
        """Small decimal float encodes correctly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(0.001)
        assert result == "0.001"

    def test_encode_float_many_decimals(self) -> None:
        """Float with many decimals encodes correctly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(3.141592653589793)
        assert result.startswith("3.14159")

    def test_encode_float_negative_small(self) -> None:
        """Small negative float encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-0.5) == "-0.5"

    def test_encode_float_returns_string(self) -> None:
        """Float encoding returns string type."""
        encoder = ValueEncoder()
        assert isinstance(encoder.encode_value(3.14), str)


class TestValueEncoderSpecialFloats:
    """Tests for special float values (NaN, Inf)."""

    def test_encode_nan(self) -> None:
        """NaN encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(float("nan")) == "null"

    def test_encode_positive_inf(self) -> None:
        """Positive infinity encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(float("inf")) == "null"

    def test_encode_negative_inf(self) -> None:
        """Negative infinity encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(float("-inf")) == "null"

    def test_encode_math_nan(self) -> None:
        """math.nan encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(math.nan) == "null"

    def test_encode_math_inf(self) -> None:
        """math.inf encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(math.inf) == "null"

    def test_encode_negative_math_inf(self) -> None:
        """Negative math.inf encodes to 'null'."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-math.inf) == "null"

    def test_encode_nan_not_string(self) -> None:
        """NaN does not encode to 'nan' string."""
        encoder = ValueEncoder()
        result = encoder.encode_value(float("nan"))
        assert result != "nan"
        assert result != "NaN"

    def test_encode_inf_not_string(self) -> None:
        """Infinity does not encode to 'inf' string."""
        encoder = ValueEncoder()
        result = encoder.encode_value(float("inf"))
        assert result != "inf"
        assert result != "Infinity"


class TestValueEncoderStrings:
    """Tests for string encoding."""

    def test_encode_string_simple(self) -> None:
        """Simple string encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("hello") == "hello"

    def test_encode_string_empty(self) -> None:
        """Empty string encodes as empty string."""
        encoder = ValueEncoder()
        assert encoder.encode_value("") == ""

    def test_encode_string_with_spaces(self) -> None:
        """String with spaces encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("hello world") == "hello world"

    def test_encode_string_with_numbers(self) -> None:
        """String with numbers encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("user123") == "user123"

    def test_encode_string_number_like(self) -> None:
        """String that looks like number encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("42") == "42"

    def test_encode_string_boolean_like(self) -> None:
        """String that looks like boolean encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("true") == "true"
        assert encoder.encode_value("false") == "false"

    def test_encode_string_null_like(self) -> None:
        """String 'null' encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("null") == "null"

    def test_encode_string_unicode(self) -> None:
        """Unicode string encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value("caf\u00e9") == "caf\u00e9"

    def test_encode_string_emoji(self) -> None:
        """String with emoji encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value("hello \U0001F600") == "hello \U0001F600"

    def test_encode_string_special_chars(self) -> None:
        """String with special characters encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("a,b:c") == "a,b:c"

    def test_encode_string_newline(self) -> None:
        """String with newline encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("line1\nline2") == "line1\nline2"

    def test_encode_string_tab(self) -> None:
        """String with tab encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("col1\tcol2") == "col1\tcol2"

    def test_encode_string_quotes(self) -> None:
        """String with quotes encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value('say "hello"') == 'say "hello"'

    def test_encode_string_backslash(self) -> None:
        """String with backslash encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("path\\to\\file") == "path\\to\\file"

    def test_encode_string_long(self) -> None:
        """Long string encodes correctly."""
        encoder = ValueEncoder()
        long_str = "a" * 10000
        assert encoder.encode_value(long_str) == long_str

    def test_encode_string_returns_string(self) -> None:
        """String encoding returns string type."""
        encoder = ValueEncoder()
        assert isinstance(encoder.encode_value("test"), str)


class TestValueEncoderUnsupportedTypes:
    """Tests for unsupported type handling."""

    def test_encode_list_raises_error(self) -> None:
        """List encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value([1, 2, 3])
        assert "list" in str(exc_info.value)

    def test_encode_dict_raises_error(self) -> None:
        """Dict encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value({"key": "value"})
        assert "dict" in str(exc_info.value)

    def test_encode_tuple_raises_error(self) -> None:
        """Tuple encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value((1, 2, 3))
        assert "tuple" in str(exc_info.value)

    def test_encode_set_raises_error(self) -> None:
        """Set encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value({1, 2, 3})
        assert "set" in str(exc_info.value)

    def test_encode_bytes_raises_error(self) -> None:
        """Bytes encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value(b"hello")
        assert "bytes" in str(exc_info.value)

    def test_encode_object_raises_error(self) -> None:
        """Object encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value(object())
        assert "object" in str(exc_info.value)

    def test_encode_class_raises_error(self) -> None:
        """Class type encoding raises TOONEncodeError."""
        encoder = ValueEncoder()

        class MyClass:
            pass

        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value(MyClass())
        assert "MyClass" in str(exc_info.value)

    def test_encode_complex_raises_error(self) -> None:
        """Complex number encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value(1 + 2j)
        assert "complex" in str(exc_info.value)

    def test_encode_function_raises_error(self) -> None:
        """Function encoding raises TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value(lambda x: x)
        assert "function" in str(exc_info.value)

    def test_error_message_contains_type_name(self) -> None:
        """Error message contains the unsupported type name."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError) as exc_info:
            encoder.encode_value({"key": "value"})
        assert "Cannot encode type:" in str(exc_info.value)
        assert "dict" in str(exc_info.value)

    def test_error_is_toon_encode_error(self) -> None:
        """Error is specifically TOONEncodeError."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError):
            encoder.encode_value([])

    def test_encode_none_type_raises_error(self) -> None:
        """NoneType object (not None) raises error."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError):
            encoder.encode_value(type(None))


class TestValueEncoderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_encode_very_small_float(self) -> None:
        """Very small float encodes without scientific notation."""
        encoder = ValueEncoder()
        result = encoder.encode_value(0.000001)
        assert "e" not in result.lower()

    def test_encode_very_large_float(self) -> None:
        """Very large float that fits in decimal encodes correctly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(1e12)
        assert result == "1000000000000"

    def test_encode_float_precision_limit(self) -> None:
        """Float precision is handled correctly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(1.0 / 3.0)
        assert result.startswith("0.3333333")

    def test_encode_bool_subclass(self) -> None:
        """Boolean check handles bool being subclass of int."""
        encoder = ValueEncoder()
        assert encoder.encode_value(True) == "true"
        assert encoder.encode_value(False) == "false"

    def test_multiple_encodings_same_encoder(self) -> None:
        """Same encoder instance handles multiple encodings."""
        encoder = ValueEncoder()
        assert encoder.encode_value(None) == "null"
        assert encoder.encode_value(True) == "true"
        assert encoder.encode_value(42) == "42"
        assert encoder.encode_value(3.14) == "3.14"
        assert encoder.encode_value("test") == "test"

    def test_encode_float_just_below_integer(self) -> None:
        """Float just below integer encodes correctly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(0.999999)
        assert "0.999999" in result

    def test_encode_float_with_exponent_form(self) -> None:
        """Float created with exponent converts properly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(2.5e3) == "2500"

    def test_encode_float_negative_exponent(self) -> None:
        """Float with negative exponent converts properly."""
        encoder = ValueEncoder()
        result = encoder.encode_value(2.5e-3)
        assert result == "0.0025"

    def test_encode_string_whitespace_only(self) -> None:
        """String with only whitespace encodes as-is."""
        encoder = ValueEncoder()
        assert encoder.encode_value("   ") == "   "

    def test_encode_string_single_char(self) -> None:
        """Single character string encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value("a") == "a"
        assert encoder.encode_value("1") == "1"
        assert encoder.encode_value(" ") == " "

    def test_encode_integer_boundary(self) -> None:
        """Integer at boundaries encodes correctly."""
        encoder = ValueEncoder()
        assert encoder.encode_value(-2147483648) == "-2147483648"
        assert encoder.encode_value(2147483647) == "2147483647"


class TestValueEncoderParametrized:
    """Parametrized tests for comprehensive coverage."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, "null"),
            (True, "true"),
            (False, "false"),
            (0, "0"),
            (1, "1"),
            (-1, "-1"),
            (42, "42"),
            (100, "100"),
            (1000000, "1000000"),
            (0.0, "0"),
            (-0.0, "0"),
            (1.0, "1"),
            (3.14, "3.14"),
            (0.5, "0.5"),
            (1e6, "1000000"),
            (float("nan"), "null"),
            (float("inf"), "null"),
            (float("-inf"), "null"),
            ("hello", "hello"),
            ("", ""),
            ("42", "42"),
            ("true", "true"),
            ("null", "null"),
        ],
    )
    def test_encode_value_parametrized(self, value: None | bool | int | float | str, expected: str) -> None:
        """Test various values encode to expected results."""
        encoder = ValueEncoder()
        assert encoder.encode_value(value) == expected

    @pytest.mark.parametrize(
        "invalid_value",
        [
            [],
            {},
            (),
            {1, 2},
            b"bytes",
            1 + 2j,
            object(),
        ],
    )
    def test_encode_unsupported_types_parametrized(self, invalid_value: object) -> None:
        """Test various unsupported types raise errors."""
        encoder = ValueEncoder()
        with pytest.raises(TOONEncodeError):
            encoder.encode_value(invalid_value)

    @pytest.mark.parametrize(
        "float_val",
        [
            1e1,
            1e2,
            1e3,
            1e4,
            1e5,
            1e6,
            1e7,
            1e8,
            1e9,
            1e10,
        ],
    )
    def test_no_scientific_notation(self, float_val: float) -> None:
        """Test that floats never use scientific notation."""
        encoder = ValueEncoder()
        result = encoder.encode_value(float_val)
        assert "e" not in result.lower()
        assert "E" not in result

    @pytest.mark.parametrize(
        "integer",
        [
            0,
            1,
            -1,
            10,
            100,
            1000,
            10000,
            100000,
            1000000,
            -100,
            -1000,
        ],
    )
    def test_integer_no_decimal(self, integer: int) -> None:
        """Test that integers never have decimal points."""
        encoder = ValueEncoder()
        result = encoder.encode_value(integer)
        assert "." not in result


class TestValueEncoderInstance:
    """Tests for ValueEncoder instance behavior."""

    def test_encoder_is_reusable(self) -> None:
        """Same encoder instance can be used multiple times."""
        encoder = ValueEncoder()
        for _ in range(100):
            assert encoder.encode_value(42) == "42"

    def test_different_encoders_same_results(self) -> None:
        """Different encoder instances produce same results."""
        encoder1 = ValueEncoder()
        encoder2 = ValueEncoder()
        values = [None, True, False, 42, 3.14, "hello"]
        for value in values:
            assert encoder1.encode_value(value) == encoder2.encode_value(value)

    def test_encoder_has_no_state(self) -> None:
        """Encoder has no mutable state between calls."""
        encoder = ValueEncoder()
        encoder.encode_value(100)
        result = encoder.encode_value(200)
        assert result == "200"
