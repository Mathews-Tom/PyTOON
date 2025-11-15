"""Validator for TOON format compliance.

This module provides the Validator class that enforces TOON v1.5 spec rules
in either strict mode (raises errors) or lenient mode (collects warnings).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytoon.utils.errors import TOONValidationError


@dataclass(frozen=True)
class ValidationWarning:
    """Represents a validation warning in lenient mode.

    Attributes:
        message: Description of the validation issue
        line: Line number where issue occurred (1-indexed)
        column: Column number where issue occurred (1-indexed)

    Examples:
        >>> warning = ValidationWarning("Array length mismatch", 5, 10)
        >>> warning.message
        'Array length mismatch'
    """

    message: str
    line: int
    column: int

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ValidationWarning({self.message!r}, line={self.line}, col={self.column})"


@dataclass
class ValidationContext:
    """Context for validation operations.

    Tracks current position and accumulates warnings in lenient mode.

    Attributes:
        line: Current line number (1-indexed)
        column: Current column number (1-indexed)
        warnings: List of warnings accumulated in lenient mode
    """

    line: int = 1
    column: int = 1
    warnings: list[ValidationWarning] = field(default_factory=list)


class Validator:
    """Validates TOON input for spec compliance.

    Enforces TOON v1.5 specification rules either strictly (raises errors)
    or leniently (collects warnings). Validates array lengths, field
    consistency, and other structural requirements.

    Args:
        strict: If True, raise errors on validation failures.
                If False, collect warnings. Default is True.

    Attributes:
        strict: Whether to operate in strict mode
        warnings: List of warnings accumulated in lenient mode

    Examples:
        >>> validator = Validator(strict=True)
        >>> validator.validate_array_length(3, 3, 1, 1)  # OK
        >>> validator.validate_array_length(3, 2, 1, 1)  # Raises error
        Traceback (most recent call last):
            ...
        pytoon.utils.errors.TOONValidationError: ...

        >>> validator = Validator(strict=False)
        >>> validator.validate_array_length(3, 2, 1, 1)  # Collects warning
        >>> len(validator.warnings)
        1

    Raises:
        TOONValidationError: In strict mode, on validation failure
    """

    def __init__(self, *, strict: bool = True) -> None:
        """Initialize the validator.

        Args:
            strict: If True, raise errors. If False, collect warnings.
        """
        self._strict = strict
        self._warnings: list[ValidationWarning] = []

    @property
    def strict(self) -> bool:
        """Get strict mode setting."""
        return self._strict

    @property
    def warnings(self) -> list[ValidationWarning]:
        """Get accumulated warnings (lenient mode only).

        Returns a copy to prevent external modification.
        """
        return self._warnings.copy()

    def validate_array_length(
        self, declared: int, actual: int, line: int, column: int
    ) -> None:
        """Validate that array length matches declared count.

        Args:
            declared: The declared array length from header
            actual: The actual number of items found
            line: Line number of array header
            column: Column number of array header

        Raises:
            TOONValidationError: In strict mode, if lengths don't match

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_array_length(3, 3, 1, 1)  # OK
            >>> v.validate_array_length(3, 2, 1, 1)  # Raises
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if declared != actual:
            message = (
                f"Array length mismatch: declared {declared} items, "
                f"found {actual} items"
            )
            self._report_issue(message, line, column)

    def validate_field_consistency(
        self,
        expected_fields: list[str],
        actual_fields: list[str],
        row_number: int,
        line: int,
        column: int,
    ) -> None:
        """Validate that tabular array row has consistent fields.

        Args:
            expected_fields: Field names from array header
            actual_fields: Field names found in current row
            row_number: Row number in array (0-indexed)
            line: Line number of row
            column: Column number of row start

        Raises:
            TOONValidationError: In strict mode, if fields don't match

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_field_consistency(["id", "name"], ["id", "name"], 0, 2, 1)
            >>> v.validate_field_consistency(["id", "name"], ["id"], 0, 2, 1)
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if len(expected_fields) != len(actual_fields):
            message = (
                f"Field count mismatch in row {row_number}: "
                f"expected {len(expected_fields)} fields, found {len(actual_fields)}"
            )
            self._report_issue(message, line, column)
            return

        for i, (expected, actual) in enumerate(zip(expected_fields, actual_fields)):
            if expected != actual:
                message = (
                    f"Field name mismatch in row {row_number}, position {i}: "
                    f"expected {expected!r}, found {actual!r}"
                )
                self._report_issue(message, line, column)
                return

    def validate_field_count(
        self,
        expected_count: int,
        actual_count: int,
        row_number: int,
        line: int,
        column: int,
    ) -> None:
        """Validate that tabular row has correct number of values.

        Args:
            expected_count: Expected number of values (from header)
            actual_count: Actual number of values in row
            row_number: Row number in array (0-indexed)
            line: Line number of row
            column: Column number of row start

        Raises:
            TOONValidationError: In strict mode, if counts don't match

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_field_count(3, 3, 0, 2, 1)  # OK
            >>> v.validate_field_count(3, 2, 0, 2, 1)  # Raises
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if expected_count != actual_count:
            message = (
                f"Value count mismatch in row {row_number}: "
                f"expected {expected_count} values, found {actual_count}"
            )
            self._report_issue(message, line, column)

    def validate_not_empty(
        self, value: str, field_name: str, line: int, column: int
    ) -> None:
        """Validate that a required field is not empty.

        Args:
            value: The value to check
            field_name: Name of the field for error message
            line: Line number
            column: Column number

        Raises:
            TOONValidationError: In strict mode, if value is empty

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_not_empty("value", "key", 1, 1)  # OK
            >>> v.validate_not_empty("", "key", 1, 1)  # Raises
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if not value:
            message = f"Required field {field_name!r} is empty"
            self._report_issue(message, line, column)

    def validate_no_duplicate_keys(
        self,
        key: str,
        existing_keys: set[str],
        line: int,
        column: int,
    ) -> None:
        """Validate that a key is not duplicated.

        Args:
            key: The key to check
            existing_keys: Set of keys already seen
            line: Line number
            column: Column number

        Raises:
            TOONValidationError: In strict mode, if key is duplicate

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_no_duplicate_keys("new", {"old"}, 1, 1)  # OK
            >>> v.validate_no_duplicate_keys("old", {"old"}, 2, 1)  # Raises
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if key in existing_keys:
            message = f"Duplicate key: {key!r}"
            self._report_issue(message, line, column)

    def validate_indent_consistency(
        self, indent: int, expected_multiple: int, line: int, column: int
    ) -> None:
        """Validate that indentation is consistent.

        Args:
            indent: Current indentation level
            expected_multiple: Expected indent unit size
            line: Line number
            column: Column number

        Raises:
            TOONValidationError: In strict mode, if indent is inconsistent

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_indent_consistency(4, 2, 1, 1)  # OK: 4 is multiple of 2
            >>> v.validate_indent_consistency(3, 2, 1, 1)  # Raises: 3 is not
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if indent % expected_multiple != 0:
            message = (
                f"Inconsistent indentation: {indent} is not a multiple "
                f"of {expected_multiple}"
            )
            self._report_issue(message, line, column)

    def validate_positive_integer(
        self, value: int, field_name: str, line: int, column: int
    ) -> None:
        """Validate that a value is a positive integer.

        Args:
            value: The value to check
            field_name: Name for error message
            line: Line number
            column: Column number

        Raises:
            TOONValidationError: In strict mode, if not positive

        Examples:
            >>> v = Validator(strict=True)
            >>> v.validate_positive_integer(5, "count", 1, 1)  # OK
            >>> v.validate_positive_integer(-1, "count", 1, 1)  # Raises
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONValidationError: ...
        """
        if value < 0:
            message = f"{field_name} must be non-negative, got {value}"
            self._report_issue(message, line, column)

    def _report_issue(self, message: str, line: int, column: int) -> None:
        """Report a validation issue.

        In strict mode, raises an error. In lenient mode, collects warning.

        Args:
            message: Description of the issue
            line: Line number
            column: Column number

        Raises:
            TOONValidationError: In strict mode
        """
        if self._strict:
            full_message = f"{message} at line {line}, column {column}"
            raise TOONValidationError(full_message)
        else:
            warning = ValidationWarning(message, line, column)
            self._warnings.append(warning)

    def clear_warnings(self) -> None:
        """Clear accumulated warnings.

        Useful for reusing validator instance.

        Examples:
            >>> v = Validator(strict=False)
            >>> v.validate_array_length(3, 2, 1, 1)
            >>> len(v.warnings)
            1
            >>> v.clear_warnings()
            >>> len(v.warnings)
            0
        """
        self._warnings.clear()

    def has_warnings(self) -> bool:
        """Check if any warnings have been accumulated.

        Returns:
            True if there are warnings, False otherwise

        Examples:
            >>> v = Validator(strict=False)
            >>> v.has_warnings()
            False
            >>> v.validate_array_length(3, 2, 1, 1)
            >>> v.has_warnings()
            True
        """
        return len(self._warnings) > 0

    def __repr__(self) -> str:
        """Return string representation."""
        mode = "strict" if self._strict else "lenient"
        warning_count = len(self._warnings)
        return f"Validator(mode={mode}, warnings={warning_count})"
