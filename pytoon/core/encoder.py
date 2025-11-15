"""Encoder class for TOON format conversion.

This module provides the Encoder class that coordinates the encoding
of Python objects to TOON format strings.
"""

from typing import Any, Literal

from pytoon.core.spec import TOONSpec
from pytoon.utils.errors import TOONEncodeError


class Encoder:
    """Encoder for converting Python objects to TOON format.

    The Encoder class provides a configurable interface for encoding Python
    objects (dicts, lists, primitives) to TOON-formatted strings. It validates
    configuration parameters and delegates actual encoding to specialized
    encoder components.

    Args:
        indent: Number of spaces per indentation level (default: 2)
        delimiter: Field delimiter for tabular arrays (default: ',')
        key_folding: Key folding mode - 'off' or 'safe' (default: 'off')
        ensure_ascii: Escape non-ASCII characters (default: False)
        sort_keys: Sort dictionary keys alphabetically (default: False)

    Raises:
        ValueError: If configuration parameters are invalid

    Examples:
        >>> encoder = Encoder()
        >>> encoder.encode({"name": "Alice"})
        'name: Alice'
        >>> encoder = Encoder(indent=4, delimiter='\\t')
        >>> encoder.encode({"key": "value"})
        'key: value'

    Note:
        This is a stub implementation. The actual encoding logic will be
        implemented in the encoder module components (TabularAnalyzer,
        ValueEncoder, ArrayEncoder, ObjectEncoder).
    """

    def __init__(
        self,
        *,
        indent: int = TOONSpec.DEFAULT_INDENT,
        delimiter: Literal[",", "\t", "|"] = TOONSpec.DEFAULT_DELIMITER,  # type: ignore[assignment]
        key_folding: Literal["off", "safe"] = "off",
        ensure_ascii: bool = False,
        sort_keys: bool = False,
    ) -> None:
        """Initialize Encoder with configuration.

        Args:
            indent: Number of spaces per indentation level (default: 2)
            delimiter: Field delimiter for tabular arrays (default: ',')
            key_folding: Key folding mode (default: 'off')
            ensure_ascii: Escape non-ASCII characters (default: False)
            sort_keys: Sort dictionary keys (default: False)

        Raises:
            ValueError: If indent <= 0 or delimiter not supported
        """
        # Validate configuration
        self._validate_config(indent, delimiter, key_folding)

        # Store configuration
        self._indent = indent
        self._delimiter = delimiter
        self._key_folding = key_folding
        self._ensure_ascii = ensure_ascii
        self._sort_keys = sort_keys

    def _validate_config(
        self,
        indent: int,
        delimiter: str,
        key_folding: str,
    ) -> None:
        """Validate configuration parameters.

        Args:
            indent: Indentation value to validate
            delimiter: Delimiter string to validate
            key_folding: Key folding mode to validate

        Raises:
            ValueError: If any parameter is invalid
        """
        TOONSpec.validate_indent(indent)
        TOONSpec.validate_delimiter(delimiter)

        if key_folding not in TOONSpec.KEY_FOLDING_MODES:
            valid = ", ".join(repr(m) for m in TOONSpec.KEY_FOLDING_MODES)
            raise ValueError(f"key_folding must be {valid}, got: {key_folding!r}")

    @property
    def indent(self) -> int:
        """Get the indentation level."""
        return self._indent

    @property
    def delimiter(self) -> str:
        """Get the field delimiter."""
        return self._delimiter

    @property
    def key_folding(self) -> str:
        """Get the key folding mode."""
        return self._key_folding

    @property
    def ensure_ascii(self) -> bool:
        """Get the ensure_ascii setting."""
        return self._ensure_ascii

    @property
    def sort_keys(self) -> bool:
        """Get the sort_keys setting."""
        return self._sort_keys

    def encode(self, value: Any) -> str:
        """Encode a Python object to TOON format.

        Args:
            value: Python object to encode (dict, list, or primitive)

        Returns:
            TOON-formatted string

        Raises:
            TOONEncodeError: If value cannot be encoded

        Examples:
            >>> encoder = Encoder()
            >>> encoder.encode({"key": "value"})
            'key: value'
            >>> encoder.encode([1, 2, 3])
            '[3]: 1,2,3'
            >>> encoder.encode(None)
            'null'

        Note:
            This is a stub implementation that handles basic types.
            Full encoding with tabular arrays, nested objects, and
            key folding will be implemented in encoder module components.
        """
        return self._encode_value(value, depth=0)

    def _encode_value(self, value: Any, depth: int) -> str:
        """Encode a single value based on its type.

        Args:
            value: Value to encode
            depth: Current nesting depth

        Returns:
            TOON-formatted string

        Raises:
            TOONEncodeError: If value type is unsupported
        """
        if depth > TOONSpec.MAX_NESTING_DEPTH:
            raise TOONEncodeError(
                f"Maximum nesting depth exceeded: {TOONSpec.MAX_NESTING_DEPTH}"
            )

        if value is None:
            return TOONSpec.NULL_VALUE

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, int):
            return str(value)

        if isinstance(value, float):
            # Handle special float values
            if value != value:  # NaN check
                return TOONSpec.NULL_VALUE
            if value == float("inf") or value == float("-inf"):
                return TOONSpec.NULL_VALUE
            # Normalize -0.0 to 0
            if value == 0.0:
                return "0"
            # No scientific notation
            result = f"{value:.15g}"
            # Only strip trailing zeros if there's a decimal point
            if "." in result:
                result = result.rstrip("0").rstrip(".")
            return result

        if isinstance(value, str):
            return self._encode_string(value)

        if isinstance(value, list):
            return self._encode_list(value, depth)

        if isinstance(value, dict):
            return self._encode_dict(value, depth)

        raise TOONEncodeError(f"Cannot encode type: {type(value)}")

    def _encode_string(self, value: str) -> str:
        """Encode a string value with appropriate quoting.

        Args:
            value: String to encode

        Returns:
            TOON-formatted string (quoted if necessary)
        """
        if TOONSpec.requires_quoting(value):
            # Escape backslashes and quotes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value

    def _encode_list(self, value: list[Any], depth: int) -> str:
        """Encode a list to TOON format.

        Args:
            value: List to encode
            depth: Current nesting depth

        Returns:
            TOON-formatted array string

        Note:
            This is a simplified implementation. Full tabular array
            detection and formatting will be in ArrayEncoder component.
        """
        if not value:
            return "[0]:"

        # Check if all items are primitives (inline array)
        all_primitives = all(
            isinstance(item, (type(None), bool, int, float, str)) for item in value
        )

        if all_primitives:
            # Inline array format: [N]: val1,val2,val3
            encoded_items = [self._encode_value(item, depth + 1) for item in value]
            return f"[{len(value)}]: {self._delimiter.join(encoded_items)}"

        # Check if all items are dicts with same keys (tabular array)
        if all(isinstance(item, dict) for item in value):
            # Check uniform keys
            first_keys = set(value[0].keys()) if value else set()
            all_uniform = all(set(item.keys()) == first_keys for item in value)

            if all_uniform and first_keys:
                # Check if all values are primitives
                all_primitive_values = all(
                    isinstance(v, (type(None), bool, int, float, str))
                    for item in value
                    for v in item.values()
                )

                if all_primitive_values:
                    # Tabular array format
                    keys = list(value[0].keys())
                    if self._sort_keys:
                        keys.sort()
                    header = f"[{len(value)}]{{{self._delimiter.join(keys)}}}:"
                    indent = " " * self._indent
                    rows = []
                    for item in value:
                        row_values = [
                            self._encode_value(item[key], depth + 1) for key in keys
                        ]
                        rows.append(f"{indent}{self._delimiter.join(row_values)}")
                    return header + "\n" + "\n".join(rows)

        # Fall back to list format (one item per line)
        indent = " " * self._indent
        lines = [f"[{len(value)}]:"]
        for item in value:
            encoded = self._encode_value(item, depth + 1)
            lines.append(f"{indent}- {encoded}")
        return "\n".join(lines)

    def _encode_dict(self, value: dict[str, Any], depth: int) -> str:
        """Encode a dictionary to TOON format.

        Args:
            value: Dictionary to encode
            depth: Current nesting depth

        Returns:
            TOON-formatted object string
        """
        if not value:
            return ""

        lines = []
        keys = list(value.keys())
        if self._sort_keys:
            keys.sort()

        indent = " " * (self._indent * depth)

        for key in keys:
            if not isinstance(key, str):
                raise TOONEncodeError(f"Dictionary keys must be strings, got: {type(key)}")

            val = value[key]
            encoded_val = self._encode_value(val, depth + 1)

            # Check if value is multiline (nested structure)
            if "\n" in encoded_val:
                lines.append(f"{indent}{key}:")
                # Indent each line of the nested value
                for line in encoded_val.split("\n"):
                    lines.append(f"{indent}{' ' * self._indent}{line}")
            else:
                lines.append(f"{indent}{key}: {encoded_val}")

        return "\n".join(lines)
