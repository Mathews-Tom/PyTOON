"""Reference decoder with schema parsing and reference resolution.

This module provides reference decoding capabilities for PyToon, enabling
decoding of relational data with shared object references from schema metadata.

Key Components:
    - ReferenceDecoder: Decoder that resolves reference placeholders to shared objects
"""

from __future__ import annotations

import re
from typing import Any

from pytoon.utils.errors import TOONDecodeError


class ReferenceDecoder:
    """Decoder that resolves reference placeholders to shared objects.

    Parses TOON strings with _schema sections and reference placeholders ($1, $2),
    reconstructing shared objects with proper Python object identity.

    Examples:
        >>> decoder = ReferenceDecoder()
        >>> toon = '''_schema:
        ...   Object1:
        ...     id: int
        ...     name: str
        ... users: [2]: $1,$2
        ... admins: [1]: $1'''
        >>> # With resolve=True, $1 and $2 become actual shared objects
        >>> result = decoder.decode_refs(toon, resolve=True)

        >>> # With resolve=False, placeholders remain as strings
        >>> result = decoder.decode_refs(toon, resolve=False)
        >>> result["users"]
        ['$1', '$2']
    """

    # Pattern to match reference placeholders like $1, $2, etc.
    _REF_PATTERN: re.Pattern[str] = re.compile(r"\$(\d+)")

    def __init__(self) -> None:
        """Initialize the ReferenceDecoder.

        Creates a new decoder instance for resolving object references.
        """
        self._ref_objects: dict[str, dict[str, Any]] = {}
        self._schema: dict[str, dict[str, str]] = {}

    def decode_refs(self, toon_string: str, resolve: bool = True) -> Any:
        """Decode TOON string with reference resolution.

        Parses a TOON string that may contain a _schema section and reference
        placeholders ($1, $2, etc.). When resolve=True, shared objects are
        reconstructed with proper Python object identity.

        Args:
            toon_string: TOON-formatted string to decode.
            resolve: If True, resolve placeholders to actual shared objects.
                    If False, keep placeholder strings in the result.

        Returns:
            Python object (dict, list, or primitive) with resolved references.
            When resolve=True, shared objects are the SAME Python object (identity).

        Raises:
            TOONDecodeError: If string cannot be parsed or references are invalid.

        Examples:
            >>> decoder = ReferenceDecoder()
            >>> toon = '''users: [2]: $1,$2
            ... admins: [1]: $1'''
            >>> result = decoder.decode_refs(toon, resolve=True)
            >>> result["users"][0] is result["admins"][0]
            True

            >>> toon = "name: Alice"
            >>> decoder.decode_refs(toon)
            {'name': 'Alice'}
        """
        self._ref_objects = {}
        self._schema = {}

        # Check if the string has a _schema section
        if toon_string.strip().startswith("_schema:"):
            return self._decode_with_schema(toon_string, resolve)

        # No schema, decode as regular TOON but still resolve references if needed
        result = self._decode_toon_value(toon_string.strip(), resolve=False)

        # If resolve is True, ensure shared identity for placeholders
        if resolve:
            result = self._resolve_references(result)

        return result

    def _decode_with_schema(self, toon_string: str, resolve: bool) -> Any:
        """Decode TOON string that contains a _schema section.

        Args:
            toon_string: TOON string with _schema section.
            resolve: Whether to resolve reference placeholders.

        Returns:
            Decoded Python object.
        """
        lines = toon_string.split("\n")
        schema_end_idx = self._parse_schema_section(lines)

        # Get the data section (everything after schema)
        data_lines = lines[schema_end_idx:]
        data_string = "\n".join(data_lines).strip()

        if not data_string:
            return {}

        # First pass: identify all reference definitions (if any)
        # In schema mode, we need to parse the data to find referenced objects
        result = self._decode_toon_value(data_string, resolve=False)

        # If resolve is True, we need to ensure shared identity
        if resolve:
            result = self._resolve_references(result)

        return result

    def _parse_schema_section(self, lines: list[str]) -> int:
        """Parse the _schema section from TOON lines.

        Args:
            lines: List of TOON lines.

        Returns:
            Index of the line after the schema section ends.
        """
        if not lines or not lines[0].strip().startswith("_schema:"):
            return 0

        idx = 1
        current_type: str | None = None

        while idx < len(lines):
            line = lines[idx]

            # Empty line or line without indentation ends schema
            if not line or (line and not line.startswith(" ")):
                break

            stripped = line.strip()
            if not stripped:
                idx += 1
                continue

            # Check indentation level
            indent_level = len(line) - len(line.lstrip())

            if indent_level == 2 and ":" in stripped:
                # Type definition line (e.g., "  Object1:")
                if stripped.endswith(":"):
                    current_type = stripped[:-1]
                    self._schema[current_type] = {}
            elif indent_level == 4 and current_type and ":" in stripped:
                # Field definition line (e.g., "    id: int")
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    field_type = parts[1].strip()
                    self._schema[current_type][field_name] = field_type

            idx += 1

        return idx

    def _decode_toon_value(self, value_string: str, resolve: bool) -> Any:
        """Decode a TOON value string to Python object.

        Args:
            value_string: TOON value string to decode.
            resolve: Whether to resolve reference placeholders.

        Returns:
            Python object (dict, list, or primitive).
        """
        value_string = value_string.strip()

        if not value_string:
            return {}

        # Check for primitives
        if value_string == "null":
            return None
        if value_string == "true":
            return True
        if value_string == "false":
            return False

        # Check for reference placeholder
        if self._REF_PATTERN.fullmatch(value_string):
            if resolve and value_string in self._ref_objects:
                return self._ref_objects[value_string]
            return value_string

        # Check for number
        try:
            if "." in value_string:
                return float(value_string)
            return int(value_string)
        except ValueError:
            pass

        # Check for quoted string
        if value_string.startswith('"') and value_string.endswith('"'):
            return self._unescape_string(value_string[1:-1])

        # Check for inline array [N]: val1,val2,val3
        inline_match = re.match(r"\[(\d+)\]:\s*(.*)$", value_string)
        if inline_match:
            count = int(inline_match.group(1))
            items_str = inline_match.group(2).strip()
            if not items_str:
                return []
            items = self._split_inline_array(items_str)
            if len(items) != count:
                raise TOONDecodeError(
                    f"Array declares {count} items but found {len(items)}"
                )
            return [self._decode_toon_value(item.strip(), resolve) for item in items]

        # Check for multiline structure (dict or array)
        if "\n" in value_string:
            return self._decode_multiline(value_string, resolve)

        # Check for dict on single line (key: value)
        if ":" in value_string and not value_string.startswith("["):
            return self._decode_dict_lines(value_string.split("\n"), resolve)

        # Default: return as string (unquoted)
        return value_string

    def _decode_multiline(self, value_string: str, resolve: bool) -> Any:
        """Decode a multiline TOON structure.

        Args:
            value_string: Multiline TOON string.
            resolve: Whether to resolve reference placeholders.

        Returns:
            Python dict or list.
        """
        lines = value_string.split("\n")
        first_line = lines[0].strip()

        # Check for array header [N]:
        array_match = re.match(r"\[(\d+)\]:(.*)$", first_line)
        if array_match:
            count = int(array_match.group(1))
            inline_part = array_match.group(2).strip()

            if inline_part:
                # Inline array
                items = self._split_inline_array(inline_part)
                if len(items) != count:
                    raise TOONDecodeError(
                        f"Array declares {count} items but found {len(items)}"
                    )
                return [self._decode_toon_value(item.strip(), resolve) for item in items]

            # List-style array with - prefix
            return self._decode_list_lines(lines[1:], count, resolve)

        # It's a dict
        return self._decode_dict_lines(lines, resolve)

    def _decode_dict_lines(self, lines: list[str], resolve: bool) -> dict[str, Any]:
        """Decode lines into a dictionary.

        Args:
            lines: Lines representing a dict structure.
            resolve: Whether to resolve reference placeholders.

        Returns:
            Python dictionary.
        """
        result: dict[str, Any] = {}
        i = 0

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            # Find key: value or key:
            colon_idx = line.find(":")
            if colon_idx == -1:
                i += 1
                continue

            key = line[:colon_idx].strip()
            value_part = line[colon_idx + 1 :].strip()

            if value_part:
                # Value on same line
                result[key] = self._decode_toon_value(value_part, resolve)
                i += 1
            else:
                # Value is nested (indented on following lines)
                nested_lines = []
                base_indent = len(lines[i]) - len(lines[i].lstrip())
                i += 1

                while i < len(lines):
                    next_line = lines[i]
                    if not next_line.strip():
                        i += 1
                        continue

                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= base_indent:
                        break

                    # Remove base indentation
                    dedented = next_line[base_indent + 2 :]  # +2 for nested indent
                    nested_lines.append(dedented)
                    i += 1

                if nested_lines:
                    nested_str = "\n".join(nested_lines)
                    result[key] = self._decode_toon_value(nested_str, resolve)
                else:
                    result[key] = {}

        return result

    def _decode_list_lines(
        self, lines: list[str], expected_count: int, resolve: bool
    ) -> list[Any]:
        """Decode lines into a list (with - prefix items).

        Args:
            lines: Lines representing list items.
            expected_count: Expected number of items.
            resolve: Whether to resolve reference placeholders.

        Returns:
            Python list.
        """
        result: list[Any] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            stripped = line.strip()
            if stripped.startswith("- "):
                # Simple item
                item_value = stripped[2:]
                result.append(self._decode_toon_value(item_value, resolve))
                i += 1
            elif stripped == "-":
                # Nested item (multiline)
                nested_lines = []
                base_indent = len(line) - len(line.lstrip())
                i += 1

                while i < len(lines):
                    next_line = lines[i]
                    if not next_line.strip():
                        i += 1
                        continue

                    next_stripped = next_line.strip()
                    if next_stripped.startswith("- "):
                        break
                    if next_stripped == "-":
                        break

                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= base_indent:
                        break

                    dedented = next_line[base_indent + 4 :]  # Remove double indent
                    nested_lines.append(dedented)
                    i += 1

                if nested_lines:
                    nested_str = "\n".join(nested_lines)
                    result.append(self._decode_toon_value(nested_str, resolve))
                else:
                    result.append({})
            else:
                i += 1

        if len(result) != expected_count:
            raise TOONDecodeError(
                f"Array declares {expected_count} items but found {len(result)}"
            )

        return result

    def _split_inline_array(self, items_str: str) -> list[str]:
        """Split inline array items by delimiter, respecting quotes.

        Args:
            items_str: Comma-separated items string.

        Returns:
            List of item strings.
        """
        items: list[str] = []
        current = ""
        in_quotes = False
        escape_next = False

        for char in items_str:
            if escape_next:
                current += char
                escape_next = False
            elif char == "\\":
                current += char
                escape_next = True
            elif char == '"':
                current += char
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                items.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            items.append(current.strip())

        return items

    def _unescape_string(self, s: str) -> str:
        """Unescape a quoted string.

        Args:
            s: String content (without outer quotes).

        Returns:
            Unescaped string.
        """
        result = ""
        i = 0
        while i < len(s):
            if s[i] == "\\" and i + 1 < len(s):
                next_char = s[i + 1]
                if next_char == "\\":
                    result += "\\"
                elif next_char == '"':
                    result += '"'
                elif next_char == "n":
                    result += "\n"
                elif next_char == "t":
                    result += "\t"
                else:
                    result += next_char
                i += 2
            else:
                result += s[i]
                i += 1
        return result

    def _resolve_references(self, data: Any) -> Any:
        """Resolve reference placeholders to ensure shared object identity.

        When the same $1 placeholder appears multiple times, this ensures
        all instances point to the same Python object.

        Args:
            data: Data structure with potential reference placeholders.

        Returns:
            Data with resolved references (same object identity).
        """
        # First pass: collect all unique references and their values
        ref_map: dict[str, Any] = {}
        self._collect_references(data, ref_map)

        # Second pass: replace placeholders with shared objects
        return self._replace_references(data, ref_map)

    def _collect_references(
        self, data: Any, ref_map: dict[str, Any]
    ) -> None:
        """Collect reference placeholders and create shared objects.

        Args:
            data: Data structure to traverse.
            ref_map: Map to populate with reference -> object mappings.
        """
        if isinstance(data, str) and self._REF_PATTERN.fullmatch(data):
            if data not in ref_map:
                # Create a shared object for this reference
                ref_map[data] = {}
        elif isinstance(data, dict):
            for value in data.values():
                self._collect_references(value, ref_map)
        elif isinstance(data, list):
            for item in data:
                self._collect_references(item, ref_map)

    def _replace_references(
        self, data: Any, ref_map: dict[str, Any]
    ) -> Any:
        """Replace reference placeholders with shared objects.

        Args:
            data: Data structure with placeholders.
            ref_map: Map of reference -> shared object.

        Returns:
            Data with replaced references.
        """
        if isinstance(data, str) and self._REF_PATTERN.fullmatch(data):
            return ref_map.get(data, data)
        if isinstance(data, dict):
            return {
                key: self._replace_references(value, ref_map)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._replace_references(item, ref_map) for item in data]
        return data
