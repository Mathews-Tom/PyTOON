"""Exception hierarchy for PyToon.

This module defines all exception types used throughout PyToon.
All exceptions inherit from TOONError for consistent error handling.
"""


class TOONError(Exception):
    """Base exception for all TOON errors.

    All PyToon exceptions inherit from this class, allowing users to catch
    all TOON-related errors with a single except clause.

    Examples:
        >>> try:
        ...     data = decode(invalid_toon)
        ... except TOONError as e:
        ...     print(f"TOON error: {e}")
    """


class TOONEncodeError(TOONError):
    """Raised when encoding fails.

    This exception is raised when a Python object cannot be encoded to TOON
    format, such as when encountering unsupported types or circular references.

    Examples:
        >>> encode(object())  # doctest: +SKIP
        TOONEncodeError: Cannot encode type: <class 'object'>
    """


class TOONDecodeError(TOONError):
    """Raised when decoding fails.

    This exception is raised when a TOON string cannot be parsed due to
    syntax errors, malformed structure, or other parsing issues.

    Examples:
        >>> decode("invalid[syntax")  # doctest: +SKIP
        TOONDecodeError: Invalid syntax at line 1: unclosed bracket
    """


class TOONValidationError(TOONDecodeError):
    """Raised when validation fails in strict mode.

    This exception is raised during strict mode decoding when the TOON
    structure violates validation rules, such as array length mismatches
    or field inconsistencies.

    Examples:
        >>> decode("items[2]{id}:\\n  1", strict=True)  # doctest: +SKIP
        TOONValidationError: Array declares 2 items but found 1
    """
