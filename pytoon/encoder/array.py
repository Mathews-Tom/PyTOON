"""ArrayEncoder class for encoding Python lists to TOON format.

This module provides the ArrayEncoder class that dispatches arrays to
optimal encoding formats (tabular, inline, or list) based on data analysis.
"""

from __future__ import annotations

from typing import Any

from pytoon.encoder.quoting import QuotingEngine
from pytoon.encoder.tabular import TabularAnalyzer
from pytoon.encoder.value import ValueEncoder
from pytoon.utils.errors import TOONEncodeError


class ArrayEncoder:
    """Encodes Python lists to TOON representation with format optimization.

    The ArrayEncoder analyzes list structure and dispatches to the most
    token-efficient format:

    - **Tabular format**: For uniform lists of dicts with primitive values
        ``array[N]{field1,field2,...}:\\n  val1,val2,...``

    - **Inline format**: For lists of all primitive values
        ``array[N]: val1,val2,...``

    - **List format**: For mixed types or nested structures
        ``array[N]:\\n  - item1\\n  - item2``

    Examples:
        >>> encoder = ArrayEncoder()
        >>> encoder.encode([])
        'array[0]:'
        >>> encoder.encode(["a", "b", "c"])
        'array[3]: a,b,c'
        >>> encoder.encode([{"id": 1}, {"id": 2}])
        'array[2]{id}:\\n  1\\n  2'
    """

    def __init__(self) -> None:
        """Initialize ArrayEncoder with required sub-encoders."""
        self._value_encoder = ValueEncoder()
        self._tabular_analyzer = TabularAnalyzer()

    def encode(
        self,
        array: list[Any],
        indent: int = 2,
        delimiter: str = ",",
        current_depth: int = 0,
    ) -> str:
        """Encode a Python list to TOON representation.

        Analyzes the array structure and selects the optimal encoding format:
        - Empty array: ``array[0]:``
        - Uniform dicts with primitives: Tabular format
        - All primitives: Inline format
        - Mixed/nested: List format

        Args:
            array: Python list to encode
            indent: Number of spaces per indentation level (default: 2)
            delimiter: Field delimiter character (default: ",")
            current_depth: Current nesting depth for indentation (default: 0)

        Returns:
            TOON-formatted string representation

        Raises:
            TOONEncodeError: If array contains unsupported types

        Examples:
            >>> encoder = ArrayEncoder()
            >>> encoder.encode([])
            'array[0]:'
            >>> encoder.encode(["a", "b"])
            'array[2]: a,b'
            >>> encoder.encode([{"id": 1, "name": "Alice"}])
            'array[1]{id,name}:\\n  1,Alice'
            >>> encoder.encode([{"x": 1}, "y"])
            'array[2]:\\n  - x: 1\\n  - y'
        """
        if not isinstance(array, list):
            raise TOONEncodeError(f"Expected list, got {type(array).__name__}")

        # Handle empty array
        if not array:
            return "array[0]:"

        # Check for tabular eligibility
        is_tabular, fields, _ = self._tabular_analyzer.analyze(array)

        if is_tabular and fields:
            return self._encode_tabular(array, fields, indent, delimiter, current_depth)

        # Check if all elements are primitives
        if self._all_primitives(array):
            return self._encode_inline(array, delimiter)

        # Default to list format for mixed/nested
        return self._encode_list(array, indent, delimiter, current_depth)

    def _all_primitives(self, array: list[Any]) -> bool:
        """Check if all elements are primitive types.

        Args:
            array: List to check

        Returns:
            True if all elements are primitives (None, bool, int, float, str)
        """
        return all(isinstance(item, (type(None), bool, int, float, str)) for item in array)

    def _encode_tabular(
        self,
        array: list[dict[str, Any]],
        fields: list[str],
        indent: int,
        delimiter: str,
        current_depth: int,
    ) -> str:
        """Encode array in tabular format.

        Format: array[N]{field1,field2,...}:\\n  val1,val2,...

        Args:
            array: List of uniform dicts
            fields: List of field names (sorted)
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth

        Returns:
            Tabular-formatted TOON string
        """
        length = len(array)
        field_list = delimiter.join(fields)

        # Build header with delimiter hint for tab
        if delimiter == "\t":
            header = f"array[{length}\\t]{{{field_list}}}:"
        else:
            header = f"array[{length}]{{{field_list}}}:"

        # Build rows
        row_indent = " " * (indent * (current_depth + 1))
        rows: list[str] = []

        for obj in array:
            values: list[str] = []
            for field in fields:
                value = obj[field]
                encoded = self._value_encoder.encode_value(value)

                # Apply quoting if needed
                if isinstance(value, str) and QuotingEngine.needs_quoting(encoded, delimiter):
                    encoded = QuotingEngine.quote_string(value)

                values.append(encoded)

            row = delimiter.join(values)
            rows.append(f"{row_indent}{row}")

        return header + "\n" + "\n".join(rows)

    def _encode_inline(self, array: list[Any], delimiter: str) -> str:
        """Encode array in inline format.

        Format: array[N]: val1,val2,...

        Args:
            array: List of primitive values
            delimiter: Field delimiter

        Returns:
            Inline-formatted TOON string
        """
        length = len(array)
        values: list[str] = []

        for item in array:
            encoded = self._value_encoder.encode_value(item)

            # Apply quoting if needed
            if isinstance(item, str) and QuotingEngine.needs_quoting(encoded, delimiter):
                encoded = QuotingEngine.quote_string(item)

            values.append(encoded)

        value_string = delimiter.join(values)
        return f"array[{length}]: {value_string}"

    def _encode_list(
        self,
        array: list[Any],
        indent: int,
        delimiter: str,
        current_depth: int,
    ) -> str:
        """Encode array in list format.

        Format: array[N]:\\n  - item1\\n  - item2

        Args:
            array: List of mixed items
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth

        Returns:
            List-formatted TOON string
        """
        length = len(array)
        header = f"array[{length}]:"
        item_indent = " " * (indent * (current_depth + 1))
        items: list[str] = []

        for item in array:
            encoded_item = self._encode_list_item(item, indent, delimiter, current_depth)
            # Handle multi-line items by adding item_indent to each line
            if "\n" in encoded_item:
                item_lines = encoded_item.split("\n")
                # First line gets "- " prefix
                formatted_item = f"{item_indent}- {item_lines[0]}"
                # Subsequent lines get item_indent added (they already have relative indent)
                for line in item_lines[1:]:
                    formatted_item += f"\n{item_indent}{line}"
                items.append(formatted_item)
            else:
                items.append(f"{item_indent}- {encoded_item}")

        return header + "\n" + "\n".join(items)

    def _encode_list_item(
        self,
        item: Any,
        indent: int,
        delimiter: str,
        current_depth: int,
    ) -> str:
        """Encode a single item in list format.

        Args:
            item: Item to encode
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth

        Returns:
            Encoded item string
        """
        if isinstance(item, dict):
            return self._encode_dict_item(item, indent, delimiter, current_depth)
        elif isinstance(item, list):
            # Recursive array encoding
            nested = self.encode(item, indent, delimiter, current_depth + 1)
            return nested
        else:
            # Primitive value
            encoded = self._value_encoder.encode_value(item)
            if isinstance(item, str) and QuotingEngine.needs_quoting(encoded, delimiter):
                encoded = QuotingEngine.quote_string(item)
            return encoded

    def _encode_dict_item(
        self,
        obj: dict[str, Any],
        indent: int,
        delimiter: str,
        current_depth: int,
    ) -> str:
        """Encode a dictionary item in list format.

        For single-key dicts: key: value
        For multi-key dicts: key1: val1\\n    key2: val2 (indented)

        Args:
            obj: Dictionary to encode
            indent: Spaces per indentation level
            delimiter: Field delimiter
            current_depth: Current nesting depth

        Returns:
            Encoded dictionary string
        """
        if not obj:
            return "{}"

        parts: list[str] = []
        nested_indent = " " * (indent * (current_depth + 2))

        for i, (key, value) in enumerate(obj.items()):
            if isinstance(value, list):
                # Nested array
                encoded_value = self.encode(value, indent, delimiter, current_depth + 2)
                if "\n" in encoded_value:
                    # Multi-line array - header goes on its own line
                    array_lines = encoded_value.split("\n")
                    first_line = array_lines[0]  # e.g., "array[N]{fields}:"
                    rest_lines = array_lines[1:]

                    # Strip "array" prefix from header - just use [N]: format
                    if first_line.startswith("array"):
                        first_line = first_line[5:]  # Remove "array" prefix

                    # Compute indentation for nested array content
                    # The array header will be at nested_indent + indent (one level deeper)
                    array_content_indent = " " * (indent * (current_depth + 3))

                    if i == 0:
                        part = f"{key}{first_line}"  # e.g., "items[2]{x,y}:"
                        for line in rest_lines:
                            if line.strip():
                                part += f"\n{array_content_indent}{line.lstrip()}"
                        parts.append(part)
                    else:
                        part = f"{nested_indent}{key}{first_line}"
                        for line in rest_lines:
                            if line.strip():
                                part += f"\n{array_content_indent}{line.lstrip()}"
                        parts.append(part)
                else:
                    # Inline array
                    if i == 0:
                        parts.append(f"{key}: {encoded_value}")
                    else:
                        parts.append(f"{nested_indent}{key}: {encoded_value}")
            elif isinstance(value, dict):
                # Nested dict - recursively encode
                encoded_value = self._encode_dict_item(value, indent, delimiter, current_depth + 1)
                if i == 0:
                    parts.append(f"{key}:\n{nested_indent}{encoded_value}")
                else:
                    parts.append(f"{nested_indent}{key}:\n{nested_indent}{encoded_value}")
            else:
                # Primitive value
                encoded_value = self._value_encoder.encode_value(value)
                if isinstance(value, str) and QuotingEngine.needs_quoting(encoded_value, delimiter):
                    encoded_value = QuotingEngine.quote_string(value)

                if i == 0:
                    parts.append(f"{key}: {encoded_value}")
                else:
                    parts.append(f"{nested_indent}{key}: {encoded_value}")

        if len(obj) == 1:
            return parts[0]

        # Multi-key dict spans multiple lines
        return "\n".join(parts)
