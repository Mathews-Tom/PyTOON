"""Context-aware string quoting for TOON encoding.

This module provides the QuotingEngine class that determines when strings
need quoting and applies proper escape sequences to ensure parseability.
"""

import re
from typing import Final

from pytoon.core.spec import TOONSpec


class QuotingEngine:
    """Context-aware string quoting engine for TOON encoding.

    This class determines when string values need to be quoted to maintain
    parseability and applies proper escape sequences. It minimizes quoting
    to reduce token usage while ensuring the TOON format remains unambiguous.

    The engine uses the active delimiter to make context-aware decisions
    about when quoting is necessary.

    Examples:
        >>> engine = QuotingEngine()
        >>> engine.needs_quoting("")
        True
        >>> engine.needs_quoting("hello")
        False
        >>> engine.needs_quoting("true")
        True
        >>> engine.needs_quoting("a,b", ",")
        True
        >>> engine.quote_string("line\\nbreak")
        '"line\\\\nbreak"'
    """

    # Numeric pattern for detecting number-like strings
    _NUMERIC_PATTERN: Final[re.Pattern[str]] = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")

    # Structural characters that require quoting when present
    _STRUCTURAL_CHARS: Final[set[str]] = {"{", "}", "[", "]", ":", "\t"}

    # Escape sequences mapping: character -> escaped representation
    _ESCAPE_MAP: Final[dict[str, str]] = {
        "\\": "\\\\",  # Backslash must be first
        '"': '\\"',
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }

    @staticmethod
    def needs_quoting(value: str, delimiter: str = ",") -> bool:
        """Determine if a string value requires quoting.

        A string requires quoting when:
        - It is empty
        - It matches a reserved keyword (true, false, null)
        - It looks like a number
        - It contains the active delimiter character
        - It contains structural characters ({, }, [, ], :)
        - It contains newlines (\\n, \\r)
        - It has leading or trailing whitespace
        - It starts with "- " (list item marker)
        - It contains backslash or double quote

        Args:
            value: The string value to check
            delimiter: The active delimiter character (default: ",")

        Returns:
            True if the string needs quoting, False otherwise

        Examples:
            >>> QuotingEngine.needs_quoting("")
            True
            >>> QuotingEngine.needs_quoting("hello")
            False
            >>> QuotingEngine.needs_quoting("true")
            True
            >>> QuotingEngine.needs_quoting("false")
            True
            >>> QuotingEngine.needs_quoting("null")
            True
            >>> QuotingEngine.needs_quoting("42")
            True
            >>> QuotingEngine.needs_quoting("3.14")
            True
            >>> QuotingEngine.needs_quoting("-10")
            True
            >>> QuotingEngine.needs_quoting("a,b", ",")
            True
            >>> QuotingEngine.needs_quoting("a|b", "|")
            True
            >>> QuotingEngine.needs_quoting("a\\tb", "\\t")
            True
            >>> QuotingEngine.needs_quoting(" padded")
            True
            >>> QuotingEngine.needs_quoting("padded ")
            True
            >>> QuotingEngine.needs_quoting("- item")
            True
            >>> QuotingEngine.needs_quoting("value:with:colons")
            True
            >>> QuotingEngine.needs_quoting("has\\nline")
            True
            >>> QuotingEngine.needs_quoting('has"quote')
            True
            >>> QuotingEngine.needs_quoting("has\\\\slash")
            True
            >>> QuotingEngine.needs_quoting("[5]")
            True
            >>> QuotingEngine.needs_quoting("{key}")
            True
        """
        # Empty string always needs quoting
        if not value:
            return True

        # Check for reserved keywords (case-sensitive per TOON spec)
        if value in TOONSpec.RESERVED_TOKENS:
            return True

        # Check if it looks like a number
        if QuotingEngine._NUMERIC_PATTERN.match(value):
            return True

        # Check if it starts with a digit but isn't a valid number (e.g., UUIDs like "23672333-...")
        # These must be quoted to avoid lexer confusion
        if value and value[0].isdigit() and not QuotingEngine._NUMERIC_PATTERN.match(value):
            return True

        # Check for leading or trailing whitespace
        if value != value.strip():
            return True

        # Check for delimiter character
        if delimiter in value:
            return True

        # Check for structural characters
        if any(char in value for char in QuotingEngine._STRUCTURAL_CHARS):
            return True

        # Check for newlines
        if "\n" in value or "\r" in value:
            return True

        # Check if starts with list item marker
        if value.startswith("- "):
            return True

        # Check for hyphens (except at start for negative numbers, which are already checked)
        # UUIDs, dates, and other hyphenated strings need quoting
        if "-" in value and not value.startswith("-"):
            return True

        # Check for slashes (URLs, paths)
        if "/" in value:
            return True

        # Check for backslash or double quote
        return bool("\\" in value or '"' in value)

    @staticmethod
    def quote_string(value: str) -> str:
        """Quote a string value with proper escape sequences.

        Applies escape sequences for special characters and wraps the result
        in double quotes. The following characters are escaped:
        - \\ (backslash) -> \\\\\\\\
        - " (double quote) -> \\\\"
        - \\n (newline) -> \\\\n
        - \\r (carriage return) -> \\\\r
        - \\t (tab) -> \\\\t

        Args:
            value: The string value to quote

        Returns:
            The quoted string with escape sequences applied

        Examples:
            >>> QuotingEngine.quote_string("hello")
            '"hello"'
            >>> QuotingEngine.quote_string("")
            '""'
            >>> QuotingEngine.quote_string('say "hello"')
            '"say \\\\"hello\\\\""'
            >>> QuotingEngine.quote_string("line1\\nline2")
            '"line1\\\\nline2"'
            >>> QuotingEngine.quote_string("tab\\there")
            '"tab\\\\there"'
            >>> QuotingEngine.quote_string("back\\\\slash")
            '"back\\\\\\\\slash"'
            >>> QuotingEngine.quote_string("mixed\\r\\nlines")
            '"mixed\\\\r\\\\nlines"'
        """
        # Apply escape sequences in order (backslash first to avoid double-escaping)
        escaped = value
        for char, replacement in QuotingEngine._ESCAPE_MAP.items():
            escaped = escaped.replace(char, replacement)

        return f'"{escaped}"'

    @staticmethod
    def is_safe_identifier(key: str) -> bool:
        """Check if a key is a safe identifier for TOON.

        A safe identifier:
        - Starts with a letter or underscore
        - Contains only letters, digits, or underscores
        - Does not contain dots or special characters

        This is used for key folding decisions to ensure keys can be
        safely joined with dots.

        Args:
            key: The key string to check

        Returns:
            True if the key is a safe identifier, False otherwise

        Examples:
            >>> QuotingEngine.is_safe_identifier("name")
            True
            >>> QuotingEngine.is_safe_identifier("user_id")
            True
            >>> QuotingEngine.is_safe_identifier("_private")
            True
            >>> QuotingEngine.is_safe_identifier("item2")
            True
            >>> QuotingEngine.is_safe_identifier("123key")
            False
            >>> QuotingEngine.is_safe_identifier("key-name")
            False
            >>> QuotingEngine.is_safe_identifier("key.name")
            False
            >>> QuotingEngine.is_safe_identifier("key name")
            False
            >>> QuotingEngine.is_safe_identifier("")
            False
        """
        return TOONSpec.is_valid_identifier(key)
