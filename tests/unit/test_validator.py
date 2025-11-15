"""Unit tests for Validator class.

Tests cover:
- Strict mode validation (raises errors)
- Lenient mode validation (collects warnings)
- Array length validation
- Field consistency validation
- Error messages with line/column info
"""

import pytest

from pytoon.decoder.validator import ValidationContext, ValidationWarning, Validator
from pytoon.utils.errors import TOONValidationError


class TestValidationWarning:
    """Test ValidationWarning dataclass."""

    def test_warning_creation(self) -> None:
        """Test creating a validation warning."""
        warning = ValidationWarning("Test message", 5, 10)
        assert warning.message == "Test message"
        assert warning.line == 5
        assert warning.column == 10

    def test_warning_immutable(self) -> None:
        """Test that warnings are immutable."""
        warning = ValidationWarning("msg", 1, 1)
        with pytest.raises(AttributeError):
            warning.message = "new"  # type: ignore[misc]

    def test_warning_repr(self) -> None:
        """Test warning string representation."""
        warning = ValidationWarning("Array mismatch", 3, 7)
        r = repr(warning)
        assert "Array mismatch" in r
        assert "line=3" in r
        assert "col=7" in r


class TestValidationContext:
    """Test ValidationContext dataclass."""

    def test_default_context(self) -> None:
        """Test default context values."""
        ctx = ValidationContext()
        assert ctx.line == 1
        assert ctx.column == 1
        assert ctx.warnings == []

    def test_context_with_values(self) -> None:
        """Test context with custom values."""
        ctx = ValidationContext(line=10, column=5)
        assert ctx.line == 10
        assert ctx.column == 5

    def test_context_warnings_list(self) -> None:
        """Test adding warnings to context."""
        ctx = ValidationContext()
        warning = ValidationWarning("test", 1, 1)
        ctx.warnings.append(warning)
        assert len(ctx.warnings) == 1


class TestValidatorInit:
    """Test Validator initialization."""

    def test_default_strict_mode(self) -> None:
        """Test default strict mode."""
        v = Validator()
        assert v.strict is True

    def test_explicit_strict_mode(self) -> None:
        """Test explicit strict mode."""
        v = Validator(strict=True)
        assert v.strict is True

    def test_lenient_mode(self) -> None:
        """Test lenient mode."""
        v = Validator(strict=False)
        assert v.strict is False

    def test_initial_warnings_empty(self) -> None:
        """Test that warnings start empty."""
        v = Validator(strict=False)
        assert v.warnings == []


class TestArrayLengthValidation:
    """Test array length validation."""

    def test_valid_length_strict(self) -> None:
        """Test valid length in strict mode."""
        v = Validator(strict=True)
        v.validate_array_length(3, 3, 1, 1)  # Should not raise

    def test_valid_length_lenient(self) -> None:
        """Test valid length in lenient mode."""
        v = Validator(strict=False)
        v.validate_array_length(5, 5, 1, 1)
        assert not v.has_warnings()

    def test_invalid_length_strict(self) -> None:
        """Test invalid length raises error in strict mode."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Array length mismatch"):
            v.validate_array_length(3, 2, 1, 1)

    def test_invalid_length_lenient(self) -> None:
        """Test invalid length collects warning in lenient mode."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 5, 10)
        assert v.has_warnings()
        assert len(v.warnings) == 1
        warning = v.warnings[0]
        assert "Array length mismatch" in warning.message
        assert "declared 3" in warning.message
        assert "found 2" in warning.message
        assert warning.line == 5
        assert warning.column == 10

    def test_zero_length_valid(self) -> None:
        """Test zero length array is valid."""
        v = Validator(strict=True)
        v.validate_array_length(0, 0, 1, 1)  # Should not raise

    def test_large_length_mismatch(self) -> None:
        """Test large length mismatch."""
        v = Validator(strict=False)
        v.validate_array_length(100, 99, 1, 1)
        assert v.has_warnings()

    def test_error_includes_position(self) -> None:
        """Test that error includes line and column."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="line 10.*column 5"):
            v.validate_array_length(3, 2, 10, 5)


class TestFieldConsistencyValidation:
    """Test field consistency validation."""

    def test_valid_fields_strict(self) -> None:
        """Test valid fields in strict mode."""
        v = Validator(strict=True)
        v.validate_field_consistency(
            ["id", "name", "email"],
            ["id", "name", "email"],
            0,
            2,
            1,
        )  # Should not raise

    def test_missing_field_strict(self) -> None:
        """Test missing field raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Field count mismatch"):
            v.validate_field_consistency(
                ["id", "name", "email"], ["id", "name"], 0, 2, 1
            )

    def test_extra_field_strict(self) -> None:
        """Test extra field raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Field count mismatch"):
            v.validate_field_consistency(
                ["id", "name"], ["id", "name", "email"], 0, 2, 1
            )

    def test_wrong_field_name_strict(self) -> None:
        """Test wrong field name raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Field name mismatch"):
            v.validate_field_consistency(["id", "name"], ["id", "title"], 0, 2, 1)

    def test_field_order_matters(self) -> None:
        """Test that field order matters."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Field name mismatch"):
            v.validate_field_consistency(["id", "name"], ["name", "id"], 0, 2, 1)

    def test_missing_field_lenient(self) -> None:
        """Test missing field in lenient mode."""
        v = Validator(strict=False)
        v.validate_field_consistency(["id", "name"], ["id"], 0, 2, 1)
        assert v.has_warnings()
        assert "Field count mismatch" in v.warnings[0].message

    def test_wrong_field_name_lenient(self) -> None:
        """Test wrong field name in lenient mode."""
        v = Validator(strict=False)
        v.validate_field_consistency(["id", "name"], ["id", "title"], 0, 2, 1)
        assert v.has_warnings()
        assert "Field name mismatch" in v.warnings[0].message

    def test_row_number_in_message(self) -> None:
        """Test that row number is in error message."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="row 5"):
            v.validate_field_consistency(["id"], ["id", "extra"], 5, 10, 1)

    def test_position_in_message(self) -> None:
        """Test that position is in error message."""
        v = Validator(strict=False)
        v.validate_field_consistency(["id", "name"], ["id", "title"], 0, 15, 3)
        warning = v.warnings[0]
        assert warning.line == 15
        assert warning.column == 3


class TestFieldCountValidation:
    """Test field count validation."""

    def test_valid_count(self) -> None:
        """Test valid field count."""
        v = Validator(strict=True)
        v.validate_field_count(3, 3, 0, 1, 1)  # Should not raise

    def test_invalid_count_strict(self) -> None:
        """Test invalid count raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Value count mismatch"):
            v.validate_field_count(3, 2, 0, 1, 1)

    def test_invalid_count_lenient(self) -> None:
        """Test invalid count collects warning."""
        v = Validator(strict=False)
        v.validate_field_count(3, 4, 2, 5, 1)
        assert v.has_warnings()
        assert "row 2" in v.warnings[0].message


class TestNotEmptyValidation:
    """Test not-empty validation."""

    def test_valid_non_empty(self) -> None:
        """Test valid non-empty value."""
        v = Validator(strict=True)
        v.validate_not_empty("value", "key", 1, 1)  # Should not raise

    def test_empty_value_strict(self) -> None:
        """Test empty value raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Required field.*is empty"):
            v.validate_not_empty("", "key", 1, 1)

    def test_empty_value_lenient(self) -> None:
        """Test empty value collects warning."""
        v = Validator(strict=False)
        v.validate_not_empty("", "username", 3, 10)
        assert v.has_warnings()
        assert "username" in v.warnings[0].message


class TestDuplicateKeyValidation:
    """Test duplicate key validation."""

    def test_new_key_valid(self) -> None:
        """Test new key is valid."""
        v = Validator(strict=True)
        v.validate_no_duplicate_keys("new", {"old", "other"}, 1, 1)

    def test_duplicate_key_strict(self) -> None:
        """Test duplicate key raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Duplicate key"):
            v.validate_no_duplicate_keys("old", {"old", "new"}, 1, 1)

    def test_duplicate_key_lenient(self) -> None:
        """Test duplicate key collects warning."""
        v = Validator(strict=False)
        v.validate_no_duplicate_keys("dup", {"dup"}, 5, 1)
        assert v.has_warnings()
        assert "Duplicate key" in v.warnings[0].message
        assert "dup" in v.warnings[0].message


class TestIndentConsistencyValidation:
    """Test indentation consistency validation."""

    def test_valid_indent(self) -> None:
        """Test valid indentation."""
        v = Validator(strict=True)
        v.validate_indent_consistency(4, 2, 1, 1)  # 4 is multiple of 2
        v.validate_indent_consistency(6, 2, 1, 1)  # 6 is multiple of 2

    def test_invalid_indent_strict(self) -> None:
        """Test invalid indentation raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="Inconsistent indentation"):
            v.validate_indent_consistency(3, 2, 1, 1)  # 3 is not multiple of 2

    def test_invalid_indent_lenient(self) -> None:
        """Test invalid indentation collects warning."""
        v = Validator(strict=False)
        v.validate_indent_consistency(5, 4, 3, 1)
        assert v.has_warnings()
        assert "5" in v.warnings[0].message
        assert "4" in v.warnings[0].message


class TestPositiveIntegerValidation:
    """Test positive integer validation."""

    def test_valid_positive(self) -> None:
        """Test valid positive integer."""
        v = Validator(strict=True)
        v.validate_positive_integer(0, "count", 1, 1)
        v.validate_positive_integer(100, "count", 1, 1)

    def test_negative_strict(self) -> None:
        """Test negative value raises error."""
        v = Validator(strict=True)
        with pytest.raises(TOONValidationError, match="must be non-negative"):
            v.validate_positive_integer(-1, "count", 1, 1)

    def test_negative_lenient(self) -> None:
        """Test negative value collects warning."""
        v = Validator(strict=False)
        v.validate_positive_integer(-5, "offset", 2, 3)
        assert v.has_warnings()
        assert "-5" in v.warnings[0].message


class TestWarningManagement:
    """Test warning management methods."""

    def test_clear_warnings(self) -> None:
        """Test clearing warnings."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 1, 1)
        v.validate_array_length(5, 4, 2, 1)
        assert len(v.warnings) == 2
        v.clear_warnings()
        assert len(v.warnings) == 0

    def test_has_warnings_false(self) -> None:
        """Test has_warnings when no warnings."""
        v = Validator(strict=False)
        assert v.has_warnings() is False

    def test_has_warnings_true(self) -> None:
        """Test has_warnings after validation failure."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 1, 1)
        assert v.has_warnings() is True

    def test_multiple_warnings(self) -> None:
        """Test accumulating multiple warnings."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 1, 1)
        v.validate_not_empty("", "field", 2, 1)
        v.validate_no_duplicate_keys("dup", {"dup"}, 3, 1)
        assert len(v.warnings) == 3

    def test_warnings_copy(self) -> None:
        """Test that warnings property returns copy."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 1, 1)
        warnings = v.warnings
        warnings.append(ValidationWarning("fake", 0, 0))  # Modify copy
        assert len(v.warnings) == 1  # Original unchanged


class TestValidatorRepr:
    """Test Validator string representation."""

    def test_repr_strict_mode(self) -> None:
        """Test repr in strict mode."""
        v = Validator(strict=True)
        r = repr(v)
        assert "strict" in r
        assert "warnings=0" in r

    def test_repr_lenient_mode(self) -> None:
        """Test repr in lenient mode."""
        v = Validator(strict=False)
        r = repr(v)
        assert "lenient" in r

    def test_repr_with_warnings(self) -> None:
        """Test repr with warnings."""
        v = Validator(strict=False)
        v.validate_array_length(3, 2, 1, 1)
        v.validate_array_length(5, 4, 2, 1)
        r = repr(v)
        assert "warnings=2" in r


class TestErrorMessages:
    """Test error message formatting."""

    def test_error_has_line_info(self) -> None:
        """Test that errors include line information."""
        v = Validator(strict=True)
        try:
            v.validate_array_length(3, 2, 42, 15)
            pytest.fail("Expected TOONValidationError")
        except TOONValidationError as e:
            assert "line 42" in str(e)
            assert "column 15" in str(e)

    def test_error_has_descriptive_message(self) -> None:
        """Test that errors are descriptive."""
        v = Validator(strict=True)
        try:
            v.validate_array_length(10, 8, 1, 1)
            pytest.fail("Expected TOONValidationError")
        except TOONValidationError as e:
            assert "10" in str(e)
            assert "8" in str(e)

    def test_warning_has_position(self) -> None:
        """Test that warnings include position."""
        v = Validator(strict=False)
        v.validate_field_count(3, 2, 0, 100, 50)
        warning = v.warnings[0]
        assert warning.line == 100
        assert warning.column == 50
