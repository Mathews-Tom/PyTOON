"""ObjectEncoder for encoding Python dictionaries to TOON representation.

This module provides the ObjectEncoder class that transforms Python dictionaries
into TOON-formatted strings with proper indentation and recursive nesting support.
"""

from __future__ import annotations

from typing import Any

from pytoon.encoder.quoting import QuotingEngine
from pytoon.encoder.value import ValueEncoder
from pytoon.utils.errors import TOONEncodeError


class ObjectEncoder:
    """Encodes Python dictionaries to TOON representation.

    The ObjectEncoder transforms dictionaries into TOON format with:

    - Flat dict: ``{"key": "value"}`` -> ``key: value``
    - Nested dicts: proper indentation (2 spaces per level)
    - Arrays: delegates to ArrayEncoder
    - Empty dict: returns empty string ""
    - Preserves Python 3.7+ dict insertion order

    Examples:
        >>> encoder = ObjectEncoder()
        >>> encoder.encode({"key": "value"})
        'key: value'
        >>> encoder.encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
        >>> encoder.encode({})
        ''
    """

    def __init__(self) -> None:
        """Initialize ObjectEncoder with required sub-encoders."""
        self._value_encoder = ValueEncoder()
        self._array_encoder: Any = None  # Lazy initialization to avoid circular import

    def _get_array_encoder(self) -> Any:
        """Get or create ArrayEncoder instance (lazy initialization).

        Returns:
            ArrayEncoder instance

        Note:
            Uses lazy initialization to avoid circular import issues
            since ArrayEncoder may call ObjectEncoder for nested dicts.
        """
        if self._array_encoder is None:
            from pytoon.encoder.array import ArrayEncoder

            self._array_encoder = ArrayEncoder()
        return self._array_encoder

    def encode(
        self,
        obj: dict[str, Any],
        indent: int = 2,
        delimiter: str = ",",
        current_depth: int = 0,
    ) -> str:
        """Encode a Python dictionary to TOON representation.

        Transforms a dictionary into TOON format with proper indentation
        for nested structures. Preserves key order (Python 3.7+ guarantee).

        Args:
            obj: Python dictionary to encode
            indent: Number of spaces per indentation level (default: 2)
            delimiter: Field delimiter character (default: ",")
            current_depth: Current nesting depth for indentation (default: 0)

        Returns:
            TOON-formatted string representation. Empty string for empty dict.

        Raises:
            TOONEncodeError: If obj is not a dict or contains unsupported types

        Examples:
            >>> encoder = ObjectEncoder()
            >>> encoder.encode({})
            ''
            >>> encoder.encode({"key": "value"})
            'key: value'
            >>> encoder.encode({"name": "Alice", "age": 30})
            'name: Alice\\nage: 30'
            >>> encoder.encode({"outer": {"inner": "value"}})
            'outer:\\n  inner: value'
            >>> encoder.encode({"items": [1, 2, 3]})
            'items: array[3]: 1,2,3'
        """
        if not isinstance(obj, dict):
            raise TOONEncodeError(f"Expected dict, got {type(obj).__name__}")

        # Handle empty dict
        if not obj:
            return ""

        lines: list[str] = []
        base_indent = " " * (indent * current_depth)

        for key, value in obj.items():
            # Ensure key is a string
            if not isinstance(key, str):
                raise TOONEncodeError(f"Dict key must be string, got {type(key).__name__}")

            # Quote key if necessary
            encoded_key = self._encode_key(key, delimiter)

            # Encode value based on type
            encoded_line = self._encode_key_value(
                encoded_key, value, indent, delimiter, current_depth, base_indent
            )
            lines.append(encoded_line)

        return "\n".join(lines)

    def _encode_key(self, key: str, delimiter: str) -> str:
        """Encode a dictionary key, applying quoting if necessary.

        Args:
            key: The key string to encode
            delimiter: Field delimiter for quoting decisions

        Returns:
            Encoded key string (quoted if necessary)

        Examples:
            >>> encoder = ObjectEncoder()
            >>> encoder._encode_key("name", ",")
            'name'
            >>> encoder._encode_key("user-id", ",")
            '"user-id"'
            >>> encoder._encode_key("a:b", ",")
            '"a:b"'
        """
        if QuotingEngine.needs_quoting(key, delimiter):
            return QuotingEngine.quote_string(key)
        return key

    def _encode_key_value(
        self,
        encoded_key: str,
        value: Any,
        indent: int,
        delimiter: str,
        current_depth: int,
        base_indent: str,
    ) -> str:
        """Encode a key-value pair to TOON format.

        Args:
            encoded_key: Already encoded key string
            value: Python value to encode
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth
            base_indent: Base indentation string for current level

        Returns:
            Formatted key-value line(s)
        """
        if isinstance(value, dict):
            return self._encode_nested_dict(
                encoded_key, value, indent, delimiter, current_depth, base_indent
            )
        elif isinstance(value, list):
            return self._encode_nested_array(
                encoded_key, value, indent, delimiter, current_depth, base_indent
            )
        else:
            return self._encode_primitive_value(encoded_key, value, delimiter, base_indent)

    def _encode_nested_dict(
        self,
        encoded_key: str,
        value: dict[str, Any],
        indent: int,
        delimiter: str,
        current_depth: int,
        base_indent: str,
    ) -> str:
        """Encode a nested dictionary value.

        Args:
            encoded_key: Already encoded key string
            value: Nested dictionary to encode
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth
            base_indent: Base indentation string

        Returns:
            Formatted nested dict lines
        """
        if not value:
            # Empty nested dict
            return f"{base_indent}{encoded_key}:"

        # Recursively encode nested dict with increased depth
        nested_encoded = self.encode(value, indent, delimiter, current_depth + 1)

        if not nested_encoded:
            return f"{base_indent}{encoded_key}:"

        return f"{base_indent}{encoded_key}:\n{nested_encoded}"

    def _encode_nested_array(
        self,
        encoded_key: str,
        value: list[Any],
        indent: int,
        delimiter: str,
        current_depth: int,
        base_indent: str,
    ) -> str:
        """Encode a nested array value.

        Args:
            encoded_key: Already encoded key string
            value: Array to encode
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth
            base_indent: Base indentation string

        Returns:
            Formatted key with array value
        """
        array_encoder = self._get_array_encoder()
        encoded_array = array_encoder.encode(value, indent, delimiter, current_depth)

        # Check if array is inline (single line) or multi-line
        if "\n" in encoded_array:
            # Multi-line array - header goes on its own line with proper nesting
            # The array header becomes a value with nested content below it
            array_lines = encoded_array.split("\n")
            first_line = array_lines[0]  # e.g., "array[N]:" or "array[N]{fields}:"
            rest_lines = array_lines[1:]

            # Strip "array" prefix from header - just use [N]: format
            # e.g., "array[1]:" -> "[1]:"
            if first_line.startswith("array"):
                first_line = first_line[5:]  # Remove "array" prefix

            # Build result: key on first line, array header indented on next line
            nested_indent = " " * (indent * (current_depth + 1))
            result = f"{base_indent}{encoded_key}:\n{nested_indent}{first_line}"

            # Add rest of array lines - they already have correct indentation
            # from ArrayEncoder (relative to current_depth), just add them as-is
            for line in rest_lines:
                result += f"\n{line}"
            return result
        else:
            # Inline array (e.g., "array[3]: 1,2,3")
            return f"{base_indent}{encoded_key}: {encoded_array}"

    def _encode_primitive_value(
        self,
        encoded_key: str,
        value: Any,
        delimiter: str,
        base_indent: str,
    ) -> str:
        """Encode a primitive value (None, bool, int, float, str).

        Args:
            encoded_key: Already encoded key string
            value: Primitive value to encode
            delimiter: Field delimiter for quoting decisions
            base_indent: Base indentation string

        Returns:
            Formatted key-value line
        """
        encoded_value = self._value_encoder.encode_value(value)

        # Apply quoting if the value is a string and needs quoting
        if isinstance(value, str) and QuotingEngine.needs_quoting(encoded_value, delimiter):
            encoded_value = QuotingEngine.quote_string(value)

        return f"{base_indent}{encoded_key}: {encoded_value}"
