"""TOON v1.5+ Specification constants and patterns.

This module defines the official TOON specification as a class with
class-level attributes for easy access and documentation.
"""

import re
from typing import Final


class TOONSpec:
    """TOON v1.5+ specification constants and validation patterns.

    This class encapsulates all TOON specification rules, including version
    information, default values, supported delimiters, and regex patterns
    for parsing and validation.

    Attributes:
        VERSION: TOON specification version
        DEFAULT_INDENT: Default number of spaces per indentation level
        SUPPORTED_DELIMITERS: List of valid field delimiters
        DEFAULT_DELIMITER: Default delimiter for tabular arrays
        IDENTIFIER_PATTERN: Regex pattern for valid identifiers
        BOOLEAN_VALUES: Mapping of boolean string representations
        NULL_VALUE: String representation of null/None
        RESERVED_TOKENS: Set of tokens with special meaning in TOON

    Examples:
        >>> TOONSpec.VERSION
        '1.5'
        >>> TOONSpec.DEFAULT_INDENT
        2
        >>> TOONSpec.SUPPORTED_DELIMITERS
        [',', '\\t', '|']
        >>> bool(TOONSpec.IDENTIFIER_PATTERN.match('valid_key'))
        True
        >>> bool(TOONSpec.IDENTIFIER_PATTERN.match('123invalid'))
        False
    """

    # Version Information
    VERSION: Final[str] = "1.5"
    """TOON specification version (v1.5+)."""

    # Indentation
    DEFAULT_INDENT: Final[int] = 2
    """Default number of spaces per indentation level."""

    MIN_INDENT: Final[int] = 1
    """Minimum allowed indentation (1 space)."""

    MAX_INDENT: Final[int] = 8
    """Maximum recommended indentation (8 spaces)."""

    # Delimiters
    SUPPORTED_DELIMITERS: Final[list[str]] = [",", "\t", "|"]
    """List of valid field delimiters for tabular arrays."""

    DEFAULT_DELIMITER: Final[str] = ","
    """Default delimiter for tabular array values."""

    # Identifiers
    IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    )
    """Regex pattern for valid TOON identifiers (keys).

    Valid identifiers:
    - Start with letter or underscore
    - Contain only letters, digits, or underscores
    - No dots, spaces, or special characters

    Examples:
        - Valid: 'name', 'user_id', '_private', 'item2'
        - Invalid: '123key', 'key.name', 'key-name', 'key name'
    """

    # Array Header Pattern
    ARRAY_HEADER_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"^\[(\d+)\](?:\{([^}]+)\})?:?$"
    )
    """Regex pattern for parsing array headers.

    Groups:
        1. Array length (required)
        2. Field list (optional, for tabular arrays)

    Examples:
        - '[3]:' - inline array of 3 items
        - '[2]{id,name}:' - tabular array with 2 rows, fields id and name
    """

    # Type Conversions
    BOOLEAN_VALUES: Final[dict[str, bool]] = {
        "true": True,
        "false": False,
    }
    """Mapping of TOON boolean string representations to Python bool."""

    NULL_VALUE: Final[str] = "null"
    """String representation of None in TOON format."""

    # Key Folding
    KEY_FOLDING_MODES: Final[list[str]] = ["off", "safe"]
    """Supported key folding modes.

    - 'off': No key folding (default)
    - 'safe': Fold single-key nested objects into dotted paths
    """

    # Reserved Tokens
    RESERVED_TOKENS: Final[set[str]] = {"true", "false", "null"}
    """Set of tokens with special meaning in TOON that cannot be unquoted keys."""

    # String Quoting Rules
    QUOTE_REQUIRED_CHARS: Final[set[str]] = {
        ",",
        "\t",
        "|",
        ":",
        "[",
        "]",
        "{",
        "}",
        "\n",
        "\r",
        '"',
        "\\",
    }
    """Characters that require string quoting when present in values."""

    # Numeric Patterns
    INTEGER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^-?\d+$")
    """Regex pattern for integer values (no scientific notation)."""

    FLOAT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^-?\d+\.\d+$")
    """Regex pattern for float values (no scientific notation)."""

    # Validation
    MAX_NESTING_DEPTH: Final[int] = 100
    """Maximum nesting depth to prevent stack overflow."""

    MAX_ARRAY_LENGTH: Final[int] = 1_000_000
    """Maximum array length for validation."""

    @classmethod
    def is_valid_identifier(cls, key: str) -> bool:
        """Check if a string is a valid TOON identifier.

        Args:
            key: String to validate as identifier

        Returns:
            True if valid identifier, False otherwise

        Examples:
            >>> TOONSpec.is_valid_identifier('valid_key')
            True
            >>> TOONSpec.is_valid_identifier('123invalid')
            False
            >>> TOONSpec.is_valid_identifier('key-with-dash')
            False
        """
        return bool(cls.IDENTIFIER_PATTERN.match(key))

    @classmethod
    def is_reserved_token(cls, value: str) -> bool:
        """Check if a string is a reserved TOON token.

        Args:
            value: String to check

        Returns:
            True if reserved token, False otherwise

        Examples:
            >>> TOONSpec.is_reserved_token('true')
            True
            >>> TOONSpec.is_reserved_token('hello')
            False
        """
        return value.lower() in cls.RESERVED_TOKENS

    @classmethod
    def requires_quoting(cls, value: str) -> bool:
        """Check if a string value requires quoting in TOON.

        A value requires quoting if:
        - It is empty
        - It contains delimiter or structural characters
        - It looks like a boolean, number, or null
        - It has leading/trailing whitespace
        - It starts with '- ' (list marker)

        Args:
            value: String value to check

        Returns:
            True if quoting required, False otherwise

        Examples:
            >>> TOONSpec.requires_quoting('')
            True
            >>> TOONSpec.requires_quoting('hello')
            False
            >>> TOONSpec.requires_quoting('hello, world')
            True
            >>> TOONSpec.requires_quoting('true')
            True
            >>> TOONSpec.requires_quoting('123')
            True
        """
        if not value:
            return True

        # Check for leading/trailing whitespace
        if value != value.strip():
            return True

        # Check for structural characters
        if any(char in value for char in cls.QUOTE_REQUIRED_CHARS):
            return True

        # Check if looks like reserved token
        if value.lower() in cls.RESERVED_TOKENS:
            return True

        # Check if looks like number
        if cls.INTEGER_PATTERN.match(value) or cls.FLOAT_PATTERN.match(value):
            return True

        # Check if starts with list marker
        if value.startswith("- "):
            return True

        # Check if looks like array header
        return bool(cls.ARRAY_HEADER_PATTERN.match(value))

    @classmethod
    def validate_delimiter(cls, delimiter: str) -> None:
        """Validate that delimiter is supported.

        Args:
            delimiter: Delimiter string to validate

        Raises:
            ValueError: If delimiter not in SUPPORTED_DELIMITERS

        Examples:
            >>> TOONSpec.validate_delimiter(',')  # No error
            >>> TOONSpec.validate_delimiter(';')  # doctest: +SKIP
            ValueError: delimiter must be ',', '\\t', or '|', got: ';'
        """
        if delimiter not in cls.SUPPORTED_DELIMITERS:
            valid = ", ".join(repr(d) for d in cls.SUPPORTED_DELIMITERS)
            raise ValueError(f"delimiter must be {valid}, got: {delimiter!r}")

    @classmethod
    def validate_indent(cls, indent: int) -> None:
        """Validate that indentation is positive.

        Args:
            indent: Indentation value to validate

        Raises:
            ValueError: If indent <= 0

        Examples:
            >>> TOONSpec.validate_indent(2)  # No error
            >>> TOONSpec.validate_indent(0)  # doctest: +SKIP
            ValueError: indent must be positive integer, got: 0
        """
        if indent <= 0:
            raise ValueError(f"indent must be positive integer, got: {indent}")
