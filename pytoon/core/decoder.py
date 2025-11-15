"""Decoder class for TOON format parsing.

This module provides the Decoder class that coordinates the decoding
of TOON format strings back to Python objects.
"""

from __future__ import annotations

from typing import Any, Literal

from pytoon.core.spec import TOONSpec
from pytoon.utils.errors import TOONDecodeError, TOONValidationError


class Decoder:
    """Decoder for converting TOON format to Python objects.

    The Decoder class provides a configurable interface for parsing TOON-formatted
    strings back into Python objects (dicts, lists, primitives). It validates
    configuration parameters and delegates actual parsing to specialized
    decoder components.

    Args:
        strict: Enable strict validation mode (default: True)
        expand_paths: Path expansion mode - 'off' or 'safe' (default: 'off')

    Raises:
        ValueError: If configuration parameters are invalid

    Examples:
        >>> decoder = Decoder()
        >>> decoder.decode('name: Alice')
        {'name': 'Alice'}
        >>> decoder = Decoder(strict=False)
        >>> decoder.decode('[2]: 1,2')
        [1, 2]

    Note:
        This is a stub implementation. The actual parsing logic will be
        implemented in the decoder module components (Lexer, Parser,
        Validator, PathExpander).
    """

    def __init__(
        self,
        *,
        strict: bool = True,
        expand_paths: Literal["off", "safe"] = "off",
    ) -> None:
        """Initialize Decoder with configuration.

        Args:
            strict: Enable strict validation mode (default: True)
            expand_paths: Path expansion mode (default: 'off')

        Raises:
            ValueError: If configuration parameters are invalid
        """
        # Validate configuration
        self._validate_config(strict, expand_paths)

        # Store configuration
        self._strict = strict
        self._expand_paths = expand_paths

    def _validate_config(
        self,
        strict: bool,
        expand_paths: str,
    ) -> None:
        """Validate configuration parameters.

        Args:
            strict: Strict mode flag
            expand_paths: Path expansion mode

        Raises:
            ValueError: If any parameter is invalid
        """
        if not isinstance(strict, bool):
            raise ValueError(f"strict must be bool, got: {type(strict).__name__}")

        if expand_paths not in TOONSpec.KEY_FOLDING_MODES:
            valid = ", ".join(repr(m) for m in TOONSpec.KEY_FOLDING_MODES)
            raise ValueError(f"expand_paths must be {valid}, got: {expand_paths!r}")

    @property
    def strict(self) -> bool:
        """Get the strict validation mode."""
        return self._strict

    @property
    def expand_paths(self) -> str:
        """Get the path expansion mode."""
        return self._expand_paths

    def decode(self, toon_string: str) -> Any:
        """Decode a TOON string to Python object.

        Args:
            toon_string: TOON-formatted string to decode

        Returns:
            Python object (dict, list, or primitive)

        Raises:
            TOONDecodeError: If string cannot be parsed
            TOONValidationError: If validation fails in strict mode

        Examples:
            >>> decoder = Decoder()
            >>> decoder.decode('name: Alice')
            {'name': 'Alice'}
            >>> decoder.decode('[3]: 1,2,3')
            [1, 2, 3]
            >>> decoder.decode('null')
            >>> decoder.decode('true')
            True

        Note:
            This is a stub implementation that handles basic formats.
            Full parsing with indentation tracking, state machine,
            and validation will be implemented in decoder module components.
        """
        if not isinstance(toon_string, str):
            raise TOONDecodeError(f"Expected string, got: {type(toon_string).__name__}")

        toon_string = toon_string.strip()

        if not toon_string:
            return {}

        # Try to parse as primitive first
        primitive = self._try_parse_primitive(toon_string)
        if primitive is not None:
            return primitive[0]

        # Try to parse as array
        if toon_string.startswith("["):
            return self._parse_array(toon_string)

        # Parse as object (key-value pairs)
        return self._parse_object(toon_string)

    def _try_parse_primitive(self, value: str) -> tuple[Any, bool] | None:
        """Try to parse a string as a primitive value.

        Args:
            value: String to parse

        Returns:
            Tuple of (parsed_value, was_quoted) if primitive, None otherwise

        Note:
            Returns tuple to distinguish between parsed None and "not a primitive"
        """
        value = value.strip()

        # Check for quoted string
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            # Unescape string
            inner = value[1:-1]
            unescaped = inner.replace('\\"', '"').replace("\\\\", "\\")
            return (unescaped, True)

        # Check for null
        if value == TOONSpec.NULL_VALUE:
            return (None, False)

        # Check for boolean
        if value in TOONSpec.BOOLEAN_VALUES:
            return (TOONSpec.BOOLEAN_VALUES[value], False)

        # Check for integer
        if TOONSpec.INTEGER_PATTERN.match(value):
            return (int(value), False)

        # Check for float
        if TOONSpec.FLOAT_PATTERN.match(value):
            return (float(value), False)

        # Not a primitive that needs special handling
        # Could be an unquoted string or part of a larger structure
        return None

    def _parse_array(self, toon_string: str) -> list[Any]:
        """Parse a TOON array string.

        Args:
            toon_string: TOON array string starting with '['

        Returns:
            Python list

        Raises:
            TOONDecodeError: If array syntax is invalid
            TOONValidationError: If array length mismatch in strict mode
        """
        lines = toon_string.split("\n")
        header_line = lines[0].strip()

        # Parse array header - handle inline values after colon
        # Pattern: [N] or [N]{fields} optionally followed by : and values
        header_part = header_line
        if ":" in header_line:
            colon_idx = header_line.index(":")
            header_part = header_line[: colon_idx + 1]  # Include colon for pattern match

        match = TOONSpec.ARRAY_HEADER_PATTERN.match(header_part)
        if not match:
            raise TOONDecodeError(f"Invalid array header: {header_line}")

        declared_length = int(match.group(1))
        field_list = match.group(2)

        # Empty array
        if declared_length == 0:
            return []

        # Check if it's a tabular array (has field list)
        if field_list:
            return self._parse_tabular_array(lines, declared_length, field_list)

        # Check if inline array (single line with values after header)
        if ":" in header_line:
            colon_idx = header_line.index(":")
            values_part = header_line[colon_idx + 1 :].strip()
            if values_part:
                return self._parse_inline_array(values_part, declared_length)

        # Multi-line list format
        return self._parse_list_array(lines[1:], declared_length)

    def _parse_inline_array(self, values_str: str, declared_length: int) -> list[Any]:
        """Parse an inline array (all values on one line).

        Args:
            values_str: Comma-separated values string
            declared_length: Expected number of items

        Returns:
            Python list

        Raises:
            TOONValidationError: If length mismatch in strict mode
        """
        # Split by delimiter (default comma, but could be tab or pipe)
        # For now, try comma first, then tab, then pipe
        items: list[str] = []

        if "," in values_str:
            items = [v.strip() for v in values_str.split(",")]
        elif "\t" in values_str:
            items = [v.strip() for v in values_str.split("\t")]
        elif "|" in values_str:
            items = [v.strip() for v in values_str.split("|")]
        else:
            items = [values_str.strip()]

        if self._strict and len(items) != declared_length:
            raise TOONValidationError(
                f"Array declares {declared_length} items but found {len(items)}"
            )

        result = []
        for item in items:
            parsed = self._try_parse_primitive(item)
            if parsed is not None:
                result.append(parsed[0])
            else:
                result.append(item)

        return result

    def _parse_tabular_array(
        self, lines: list[str], declared_length: int, field_list: str
    ) -> list[dict[str, Any]]:
        """Parse a tabular array (objects with uniform keys).

        Args:
            lines: All lines including header
            declared_length: Expected number of rows
            field_list: Comma-separated field names

        Returns:
            List of dictionaries

        Raises:
            TOONValidationError: If validation fails in strict mode
        """
        # Parse field names (handle different delimiters)
        if "," in field_list:
            fields = [f.strip() for f in field_list.split(",")]
        elif "\t" in field_list:
            fields = [f.strip() for f in field_list.split("\t")]
        elif "|" in field_list:
            fields = [f.strip() for f in field_list.split("|")]
        else:
            fields = [field_list.strip()]

        result = []
        data_lines = [line.strip() for line in lines[1:] if line.strip()]

        if self._strict and len(data_lines) != declared_length:
            raise TOONValidationError(
                f"Array declares {declared_length} rows but found {len(data_lines)}"
            )

        for line in data_lines:
            # Split values by delimiter
            if "," in line:
                values = [v.strip() for v in line.split(",")]
            elif "\t" in line:
                values = [v.strip() for v in line.split("\t")]
            elif "|" in line:
                values = [v.strip() for v in line.split("|")]
            else:
                values = [line.strip()]

            if self._strict and len(values) != len(fields):
                raise TOONValidationError(
                    f"Row has {len(values)} values but expected {len(fields)} fields"
                )

            # Build object
            obj: dict[str, Any] = {}
            for i, field in enumerate(fields):
                if i < len(values):
                    parsed = self._try_parse_primitive(values[i])
                    if parsed is not None:
                        obj[field] = parsed[0]
                    else:
                        obj[field] = values[i]
                else:
                    obj[field] = None

            result.append(obj)

        return result

    def _parse_list_array(self, data_lines: list[str], declared_length: int) -> list[Any]:
        """Parse a list-style array (one item per line with '- ' prefix).

        Args:
            data_lines: Lines after the header
            declared_length: Expected number of items

        Returns:
            Python list

        Raises:
            TOONValidationError: If length mismatch in strict mode
        """
        result = []

        for line in data_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("- "):
                item_str = line[2:].strip()
                parsed = self._try_parse_primitive(item_str)
                if parsed is not None:
                    result.append(parsed[0])
                else:
                    result.append(item_str)

        if self._strict and len(result) != declared_length:
            raise TOONValidationError(
                f"Array declares {declared_length} items but found {len(result)}"
            )

        return result

    def _parse_object(self, toon_string: str) -> dict[str, Any]:
        """Parse a TOON object (key-value pairs).

        Args:
            toon_string: TOON object string

        Returns:
            Python dictionary

        Raises:
            TOONDecodeError: If syntax is invalid
        """
        result: dict[str, Any] = {}
        lines = toon_string.split("\n")

        current_key = None
        current_value_lines: list[str] = []
        base_indent = 0

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Calculate indentation
            indent = len(line) - len(line.lstrip())

            # Check if this is a key-value line
            if ":" in line:
                stripped = line.strip()
                colon_idx = stripped.index(":")

                # Check if this is a key: value pair
                key_part = stripped[:colon_idx]
                value_part = stripped[colon_idx + 1 :].strip()

                # Validate key is valid identifier
                if TOONSpec.is_valid_identifier(key_part):
                    # Save previous key-value if exists
                    if current_key is not None:
                        if current_value_lines:
                            # Parse nested value
                            nested_str = "\n".join(current_value_lines)
                            result[current_key] = self.decode(nested_str)
                        else:
                            result[current_key] = ""

                    current_key = key_part

                    if value_part:
                        # Inline value
                        parsed = self._try_parse_primitive(value_part)
                        if parsed is not None:
                            result[current_key] = parsed[0]
                        else:
                            # Check if it's an array header
                            if value_part.startswith("["):
                                # Collect remaining lines for array
                                remaining = "\n".join([value_part, *lines[i + 1 :]])
                                result[current_key] = self._parse_array(remaining)
                                return result
                            else:
                                result[current_key] = value_part
                        current_key = None
                        current_value_lines = []
                    else:
                        # Value on next lines (nested structure)
                        current_value_lines = []
                        base_indent = indent
                else:
                    # Not a valid key, might be part of nested value
                    if current_key is not None:
                        current_value_lines.append(line)
            else:
                # Line without colon, might be part of nested structure
                if current_key is not None:
                    current_value_lines.append(line)

        # Handle last key-value
        if current_key is not None:
            if current_value_lines:
                nested_str = "\n".join(current_value_lines)
                result[current_key] = self.decode(nested_str)
            else:
                result[current_key] = ""

        return result
