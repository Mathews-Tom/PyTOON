"""Unit tests for validation helper functions."""

from __future__ import annotations

import pytest

from pytoon.utils.validation import (
    is_safe_identifier,
    validate_delimiter,
    validate_expand_paths_mode,
    validate_indent,
    validate_key_folding_mode,
)


class TestValidateIndent:
    """Tests for validate_indent function."""

    def test_valid_indent_default(self) -> None:
        """Default indent of 2 should be valid."""
        validate_indent(2)  # Should not raise

    def test_valid_indent_one(self) -> None:
        """Minimum indent of 1 should be valid."""
        validate_indent(1)  # Should not raise

    def test_valid_indent_four(self) -> None:
        """Common indent of 4 should be valid."""
        validate_indent(4)  # Should not raise

    def test_valid_indent_large(self) -> None:
        """Large indent should be valid."""
        validate_indent(100)  # Should not raise

    def test_invalid_indent_zero(self) -> None:
        """Indent of 0 should raise ValueError."""
        with pytest.raises(ValueError, match="indent must be a positive integer"):
            validate_indent(0)

    def test_invalid_indent_negative(self) -> None:
        """Negative indent should raise ValueError."""
        with pytest.raises(ValueError, match="indent must be a positive integer"):
            validate_indent(-1)

    def test_invalid_indent_large_negative(self) -> None:
        """Large negative indent should raise ValueError."""
        with pytest.raises(ValueError, match="indent must be a positive integer"):
            validate_indent(-100)

    def test_error_message_includes_value(self) -> None:
        """Error message should include the invalid value."""
        with pytest.raises(ValueError, match="got: -5"):
            validate_indent(-5)


class TestValidateDelimiter:
    """Tests for validate_delimiter function."""

    def test_valid_delimiter_comma(self) -> None:
        """Comma delimiter should be valid."""
        validate_delimiter(",")  # Should not raise

    def test_valid_delimiter_tab(self) -> None:
        """Tab delimiter should be valid."""
        validate_delimiter("\t")  # Should not raise

    def test_valid_delimiter_pipe(self) -> None:
        """Pipe delimiter should be valid."""
        validate_delimiter("|")  # Should not raise

    def test_invalid_delimiter_semicolon(self) -> None:
        """Semicolon should not be valid delimiter."""
        with pytest.raises(ValueError, match="delimiter must be one of"):
            validate_delimiter(";")

    def test_invalid_delimiter_space(self) -> None:
        """Space should not be valid delimiter."""
        with pytest.raises(ValueError, match="delimiter must be one of"):
            validate_delimiter(" ")

    def test_invalid_delimiter_empty(self) -> None:
        """Empty string should not be valid delimiter."""
        with pytest.raises(ValueError, match="delimiter must be one of"):
            validate_delimiter("")

    def test_invalid_delimiter_colon(self) -> None:
        """Colon should not be valid delimiter."""
        with pytest.raises(ValueError, match="delimiter must be one of"):
            validate_delimiter(":")

    def test_invalid_delimiter_multiple_chars(self) -> None:
        """Multiple character string should not be valid."""
        with pytest.raises(ValueError, match="delimiter must be one of"):
            validate_delimiter(",,")

    def test_error_message_includes_value(self) -> None:
        """Error message should include the invalid value."""
        with pytest.raises(ValueError, match="got: ';'"):
            validate_delimiter(";")

    def test_error_message_lists_valid_options(self) -> None:
        """Error message should list valid options."""
        with pytest.raises(ValueError, match=r"','.*'\\t'.*'\|'"):
            validate_delimiter("X")


class TestIsSafeIdentifier:
    """Tests for is_safe_identifier function."""

    def test_simple_lowercase_name(self) -> None:
        """Simple lowercase name should be safe."""
        assert is_safe_identifier("name") is True

    def test_camel_case_name(self) -> None:
        """CamelCase name should be safe."""
        assert is_safe_identifier("userId") is True

    def test_snake_case_name(self) -> None:
        """Snake_case name should be safe."""
        assert is_safe_identifier("item_count") is True

    def test_name_with_trailing_number(self) -> None:
        """Name with trailing number should be safe."""
        assert is_safe_identifier("data2") is True

    def test_uppercase_name(self) -> None:
        """Uppercase name should be safe."""
        assert is_safe_identifier("CONFIG") is True

    def test_mixed_case_with_underscore(self) -> None:
        """Mixed case with underscore should be safe."""
        assert is_safe_identifier("myVar_name") is True

    def test_single_letter(self) -> None:
        """Single letter should be safe."""
        assert is_safe_identifier("x") is True

    def test_leading_underscore_not_safe(self) -> None:
        """Leading underscore should NOT be safe (private key)."""
        assert is_safe_identifier("_private") is False

    def test_double_leading_underscore_not_safe(self) -> None:
        """Double leading underscore should NOT be safe."""
        assert is_safe_identifier("__dunder") is False

    def test_trailing_underscore_is_safe(self) -> None:
        """Trailing underscore should be safe."""
        assert is_safe_identifier("class_") is True

    def test_dot_in_key_not_safe(self) -> None:
        """Key with dot should NOT be safe (folding ambiguity)."""
        assert is_safe_identifier("key.name") is False

    def test_multiple_dots_not_safe(self) -> None:
        """Key with multiple dots should NOT be safe."""
        assert is_safe_identifier("a.b.c") is False

    def test_starts_with_digit_not_safe(self) -> None:
        """Key starting with digit should NOT be safe."""
        assert is_safe_identifier("123key") is False

    def test_empty_string_not_safe(self) -> None:
        """Empty string should NOT be safe."""
        assert is_safe_identifier("") is False

    def test_dash_in_key_not_safe(self) -> None:
        """Key with dash should NOT be safe."""
        assert is_safe_identifier("key-name") is False

    def test_space_in_key_not_safe(self) -> None:
        """Key with space should NOT be safe."""
        assert is_safe_identifier("key name") is False

    def test_special_chars_not_safe(self) -> None:
        """Key with special characters should NOT be safe."""
        assert is_safe_identifier("key@value") is False
        assert is_safe_identifier("key#1") is False
        assert is_safe_identifier("key$var") is False

    def test_colon_not_safe(self) -> None:
        """Key with colon should NOT be safe."""
        assert is_safe_identifier("key:value") is False

    def test_only_underscores_not_safe(self) -> None:
        """String of only underscores (starts with _) should NOT be safe."""
        assert is_safe_identifier("___") is False

    def test_numeric_string_not_safe(self) -> None:
        """Purely numeric string should NOT be safe."""
        assert is_safe_identifier("123") is False


class TestValidateKeyFoldingMode:
    """Tests for validate_key_folding_mode function."""

    def test_valid_mode_off(self) -> None:
        """'off' mode should be valid."""
        validate_key_folding_mode("off")  # Should not raise

    def test_valid_mode_safe(self) -> None:
        """'safe' mode should be valid."""
        validate_key_folding_mode("safe")  # Should not raise

    def test_invalid_mode_auto(self) -> None:
        """'auto' mode should be invalid."""
        with pytest.raises(ValueError, match="key_folding must be one of"):
            validate_key_folding_mode("auto")

    def test_invalid_mode_on(self) -> None:
        """'on' mode should be invalid."""
        with pytest.raises(ValueError, match="key_folding must be one of"):
            validate_key_folding_mode("on")

    def test_invalid_mode_empty(self) -> None:
        """Empty string should be invalid."""
        with pytest.raises(ValueError, match="key_folding must be one of"):
            validate_key_folding_mode("")

    def test_error_message_includes_value(self) -> None:
        """Error message should include the invalid value."""
        with pytest.raises(ValueError, match="got: 'invalid'"):
            validate_key_folding_mode("invalid")

    def test_case_sensitive(self) -> None:
        """Mode validation should be case-sensitive."""
        with pytest.raises(ValueError, match="key_folding must be one of"):
            validate_key_folding_mode("OFF")
        with pytest.raises(ValueError, match="key_folding must be one of"):
            validate_key_folding_mode("Safe")


class TestValidateExpandPathsMode:
    """Tests for validate_expand_paths_mode function."""

    def test_valid_mode_off(self) -> None:
        """'off' mode should be valid."""
        validate_expand_paths_mode("off")  # Should not raise

    def test_valid_mode_safe(self) -> None:
        """'safe' mode should be valid."""
        validate_expand_paths_mode("safe")  # Should not raise

    def test_invalid_mode_auto(self) -> None:
        """'auto' mode should be invalid."""
        with pytest.raises(ValueError, match="expand_paths must be one of"):
            validate_expand_paths_mode("auto")

    def test_invalid_mode_on(self) -> None:
        """'on' mode should be invalid."""
        with pytest.raises(ValueError, match="expand_paths must be one of"):
            validate_expand_paths_mode("on")

    def test_invalid_mode_empty(self) -> None:
        """Empty string should be invalid."""
        with pytest.raises(ValueError, match="expand_paths must be one of"):
            validate_expand_paths_mode("")

    def test_error_message_includes_value(self) -> None:
        """Error message should include the invalid value."""
        with pytest.raises(ValueError, match="got: 'invalid'"):
            validate_expand_paths_mode("invalid")


class TestErrorMessageConsistency:
    """Test that all error messages follow consistent format."""

    def test_indent_error_format(self) -> None:
        """Indent errors should follow standard format."""
        with pytest.raises(ValueError) as exc_info:
            validate_indent(-1)
        msg = str(exc_info.value)
        assert "indent must be" in msg
        assert "got:" in msg

    def test_delimiter_error_format(self) -> None:
        """Delimiter errors should follow standard format."""
        with pytest.raises(ValueError) as exc_info:
            validate_delimiter("X")
        msg = str(exc_info.value)
        assert "delimiter must be" in msg
        assert "got:" in msg

    def test_key_folding_error_format(self) -> None:
        """Key folding errors should follow standard format."""
        with pytest.raises(ValueError) as exc_info:
            validate_key_folding_mode("bad")
        msg = str(exc_info.value)
        assert "key_folding must be" in msg
        assert "got:" in msg

    def test_expand_paths_error_format(self) -> None:
        """Expand paths errors should follow standard format."""
        with pytest.raises(ValueError) as exc_info:
            validate_expand_paths_mode("bad")
        msg = str(exc_info.value)
        assert "expand_paths must be" in msg
        assert "got:" in msg


class TestIntegrationWithUtils:
    """Test that validation functions are properly exported."""

    def test_import_from_utils_module(self) -> None:
        """Should be able to import from pytoon.utils."""
        from pytoon.utils import (
            is_safe_identifier,
            validate_delimiter,
            validate_indent,
        )

        # Verify they work
        validate_indent(2)
        validate_delimiter(",")
        assert is_safe_identifier("test") is True

    def test_import_from_validation_module(self) -> None:
        """Should be able to import directly from validation module."""
        from pytoon.utils.validation import (
            is_safe_identifier,
            validate_delimiter,
            validate_indent,
        )

        # Verify they work
        validate_indent(4)
        validate_delimiter("\t")
        assert is_safe_identifier("key") is True
