"""ValueEncoder for normalizing Python primitives to TOON representation.

This module provides the ValueEncoder class that transforms Python primitive
values (None, bool, int, float, str) into their TOON string representations.
"""

from __future__ import annotations

import math
from typing import Any

from pytoon.utils.errors import TOONEncodeError


class ValueEncoder:
    """Encodes Python primitive values to TOON representation.

    The ValueEncoder normalizes Python primitives according to TOON v1.5+
    specification rules:

    - None -> "null"
    - bool -> lowercase "true" or "false"
    - int -> decimal string representation
    - float -> decimal string (no scientific notation)
    - float('nan') or float('inf') -> "null"
    - -0.0 -> "0" (normalized to positive zero)
    - str -> string as-is (quoting handled by QuotingEngine)

    Examples:
        >>> encoder = ValueEncoder()
        >>> encoder.encode_value(None)
        'null'
        >>> encoder.encode_value(True)
        'true'
        >>> encoder.encode_value(1e6)
        '1000000'
        >>> encoder.encode_value(float('nan'))
        'null'
    """

    def encode_value(self, value: Any) -> str:
        """Encode a Python primitive value to TOON representation.

        Args:
            value: Python primitive (None, bool, int, float, str)

        Returns:
            TOON-formatted string representation

        Raises:
            TOONEncodeError: If value is of unsupported type

        Type Conversions:
            - None -> "null"
            - True -> "true"
            - False -> "false"
            - int -> decimal string
            - float -> decimal string without scientific notation
            - float('nan') -> "null"
            - float('inf') -> "null"
            - float('-inf') -> "null"
            - -0.0 -> "0"
            - str -> string as-is

        Examples:
            >>> encoder = ValueEncoder()
            >>> encoder.encode_value(None)
            'null'
            >>> encoder.encode_value(True)
            'true'
            >>> encoder.encode_value(False)
            'false'
            >>> encoder.encode_value(42)
            '42'
            >>> encoder.encode_value(3.14)
            '3.14'
            >>> encoder.encode_value(1e6)
            '1000000'
            >>> encoder.encode_value(-0.0)
            '0'
            >>> encoder.encode_value("hello")
            'hello'
        """
        if value is None:
            return "null"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, int):
            return str(value)

        if isinstance(value, float):
            return self._encode_float(value)

        if isinstance(value, str):
            return value

        raise TOONEncodeError(f"Cannot encode type: {type(value).__name__}")

    def _encode_float(self, value: float) -> str:
        """Encode a float value without scientific notation.

        Args:
            value: Float value to encode

        Returns:
            TOON-formatted string representation

        Special cases:
            - NaN -> "null"
            - +/-Inf -> "null"
            - -0.0 -> "0"
            - No scientific notation (1e6 -> "1000000")
            - Trailing zeros removed (3.140 -> "3.14")
            - Trailing decimal point removed (3. -> "3")
        """
        if math.isnan(value) or math.isinf(value):
            return "null"

        if value == 0.0:
            return "0"

        if value == int(value) and abs(value) < 1e15:
            return str(int(value))

        formatted = f"{value:.15f}"
        formatted = formatted.rstrip("0").rstrip(".")

        return formatted
