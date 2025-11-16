"""Graph encoder and decoder for circular reference handling.

This module provides graph encoding and decoding capabilities for PyToon,
enabling support for circular references (v1.2) where objects reference
each other in cycles.

Key Components:
    - GraphEncoder: Encoder that handles circular references with object IDs
    - GraphDecoder: Decoder that reconstructs circular Python references
"""

from __future__ import annotations

import re
from typing import Any

from pytoon.utils.errors import TOONDecodeError, TOONEncodeError


class GraphEncoder:
    """Encoder that handles circular references with object ID assignment.

    Traverses data structures using Python id() tracking to detect circular
    references before recursion occurs. Assigns unique object IDs ($ref:1, $ref:2)
    to objects and replaces circular back-references with placeholders.

    The encoding process is O(n) where n is the total number of objects,
    using a hash map for id() tracking to prevent infinite recursion.

    Examples:
        >>> encoder = GraphEncoder()
        >>> user1 = {"id": 1, "name": "Alice"}
        >>> user2 = {"id": 2, "name": "Bob"}
        >>> user1["friend"] = user2
        >>> user2["friend"] = user1  # Circular reference
        >>> result = encoder.encode_graph({"users": [user1, user2]})
        >>> "_graph: true" in result
        True
        >>> "$ref:" in result
        True

        >>> # Self-referencing object
        >>> obj = {"id": 1}
        >>> obj["self"] = obj
        >>> result = encoder.encode_graph(obj)
        >>> "$ref:" in result
        True
    """

    def __init__(self) -> None:
        """Initialize the GraphEncoder.

        Creates a new encoder instance for handling circular references.
        """
        self._id_counter: int = 0
        self._id_map: dict[int, int] = {}  # Python id() -> assigned object ID
        self._encoded_ids: set[int] = set()  # Object IDs that have been fully encoded

    def encode_graph(
        self,
        data: Any,
        *,
        indent: int = 2,
        delimiter: str = ",",
    ) -> str:
        """Encode data with circular reference handling.

        Detects circular references in the data and encodes them using
        object ID placeholders ($ref:1, $ref:2, etc.). Adds _graph: true
        flag to indicate graph mode encoding.

        Args:
            data: Python object to encode (dict, list, or primitive).
            indent: Number of spaces per indentation level (default: 2).
            delimiter: Field delimiter for inline arrays (default: ',').

        Returns:
            TOON-formatted string with _graph: true flag and $ref:N placeholders.

        Raises:
            TOONEncodeError: If encoding fails due to unsupported types.

        Examples:
            >>> encoder = GraphEncoder()
            >>> user1 = {"id": 1}
            >>> user2 = {"id": 2}
            >>> user1["friend"] = user2
            >>> user2["friend"] = user1
            >>> result = encoder.encode_graph({"users": [user1, user2]})
            >>> "_graph: true" in result
            True

            >>> # Simple case without cycles still works
            >>> result = encoder.encode_graph({"a": 1, "b": 2})
            >>> "_graph: true" in result
            True
            >>> "$ref:" not in result
            True
        """
        self._id_counter = 0
        self._id_map = {}
        self._encoded_ids = set()

        try:
            # First pass: assign IDs to all compound objects
            self._assign_ids(data)

            # Second pass: encode with cycle detection
            encoded_data = self._encode_value(data, 0, indent, delimiter)

            # Add _graph: true flag
            return f"_graph: true\n{encoded_data}"

        except RecursionError as e:
            raise TOONEncodeError(
                f"Maximum recursion depth exceeded during graph encoding: {e}"
            ) from e
        except TOONEncodeError:
            raise
        except Exception as e:
            raise TOONEncodeError(f"Error during graph encoding: {e}") from e

    def _assign_ids(self, obj: Any) -> None:
        """Assign unique IDs to all compound objects during first pass.

        Args:
            obj: Object to traverse and assign IDs.
        """
        if isinstance(obj, dict):
            obj_id = id(obj)
            if obj_id in self._id_map:
                return  # Already assigned

            self._id_counter += 1
            self._id_map[obj_id] = self._id_counter

            for value in obj.values():
                self._assign_ids(value)

        elif isinstance(obj, list):
            obj_id = id(obj)
            if obj_id in self._id_map:
                return  # Already assigned

            self._id_counter += 1
            self._id_map[obj_id] = self._id_counter

            for item in obj:
                self._assign_ids(item)

    def _encode_value(
        self,
        value: Any,
        depth: int,
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a value, detecting circular references.

        Args:
            value: Value to encode.
            depth: Current nesting depth.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted string.
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if value != value or value == float("inf") or value == float("-inf"):
                return "null"
            if value == 0.0:
                return "0"
            result = f"{value:.15g}"
            if "." in result:
                result = result.rstrip("0").rstrip(".")
            return result
        if isinstance(value, str):
            return self._encode_string(value)
        if isinstance(value, list):
            return self._encode_list(value, depth, indent, delimiter)
        if isinstance(value, dict):
            return self._encode_dict(value, depth, indent, delimiter)

        raise TOONEncodeError(f"Cannot encode type: {type(value)}")

    def _encode_string(self, value: str) -> str:
        """Encode a string value with quoting if necessary.

        Args:
            value: String to encode.

        Returns:
            TOON-formatted string.
        """
        from pytoon.core.spec import TOONSpec

        if TOONSpec.requires_quoting(value):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value

    def _encode_list(
        self,
        value: list[Any],
        depth: int,
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a list with circular reference detection.

        Args:
            value: List to encode.
            depth: Current nesting depth.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted array string.
        """
        obj_id = id(value)
        assigned_id = self._id_map.get(obj_id)

        # Check for circular reference (already being encoded)
        if assigned_id is not None and obj_id in self._encoded_ids:
            return f"$ref:{assigned_id}"

        # Mark as being encoded to detect cycles
        if assigned_id is not None:
            self._encoded_ids.add(obj_id)

        if not value:
            return "[0]:"

        # Check if all items are primitives or simple references
        all_simple = all(
            isinstance(item, (type(None), bool, int, float, str))
            or (isinstance(item, (dict, list)) and id(item) in self._encoded_ids)
            for item in value
        )

        if all_simple:
            encoded_items = [
                self._encode_value(item, depth + 1, indent, delimiter) for item in value
            ]
            return f"[{len(value)}]: {delimiter.join(encoded_items)}"

        # List format - use single indent for items (not cumulative)
        indent_str = " " * indent
        lines = [f"[{len(value)}]:"]
        for item in value:
            encoded = self._encode_value(item, depth + 1, indent, delimiter)
            if "\n" in encoded:
                lines.append(f"{indent_str}-")
                for line in encoded.split("\n"):
                    if line.strip():
                        lines.append(f"{indent_str}{indent_str}{line}")
            else:
                lines.append(f"{indent_str}- {encoded}")
        return "\n".join(lines)

    def _encode_dict(
        self,
        value: dict[str, Any],
        depth: int,
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a dictionary with circular reference detection.

        Args:
            value: Dictionary to encode.
            depth: Current nesting depth.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted object string.
        """
        obj_id = id(value)
        assigned_id = self._id_map.get(obj_id)

        # Check for circular reference (already being encoded)
        if assigned_id is not None and obj_id in self._encoded_ids:
            return f"$ref:{assigned_id}"

        # Mark as being encoded to detect cycles
        if assigned_id is not None:
            self._encoded_ids.add(obj_id)

        if not value:
            return ""

        lines: list[str] = []
        # Use single indent level (not cumulative based on depth)
        indent_str = ""  # No prefix indent for dict keys

        for key, val in value.items():
            if not isinstance(key, str):
                raise TOONEncodeError(
                    f"Dictionary keys must be strings, got: {type(key)}"
                )

            encoded_val = self._encode_value(val, depth + 1, indent, delimiter)

            if "\n" in encoded_val:
                lines.append(f"{indent_str}{key}:")
                for line in encoded_val.split("\n"):
                    if line.strip():
                        lines.append(f"{' ' * indent}{line}")
            else:
                lines.append(f"{indent_str}{key}: {encoded_val}")

        return "\n".join(lines)


class GraphDecoder:
    """Decoder that reconstructs circular Python references.

    Parses TOON strings with _graph: true flag and $ref:N placeholders,
    reconstructing circular references in Python objects. Uses a two-pass
    approach: first builds object shells, then populates them.

    Examples:
        >>> decoder = GraphDecoder()
        >>> toon = '''_graph: true
        ... user1:
        ...   id: 1
        ...   friend: $ref:2
        ... user2:
        ...   id: 2
        ...   friend: $ref:1'''
        >>> result = decoder.decode_graph(toon)
        >>> result["user1"]["friend"] is result["user2"]
        True
        >>> result["user2"]["friend"] is result["user1"]
        True

        >>> # Self-referencing
        >>> toon = '''_graph: true
        ... obj:
        ...   id: 1
        ...   self: $ref:1'''
        >>> result = decoder.decode_graph(toon)
        >>> result["obj"]["self"] is result["obj"]
        True
    """

    # Pattern to match graph reference placeholders like $ref:1, $ref:2, etc.
    _GRAPH_REF_PATTERN: re.Pattern[str] = re.compile(r"\$ref:(\d+)")

    def __init__(self) -> None:
        """Initialize the GraphDecoder.

        Creates a new decoder instance for reconstructing circular references.
        """
        self._object_registry: dict[int, Any] = {}  # ID -> Python object
        self._pending_refs: list[tuple[Any, str | int, int]] = []  # (container, key, ref_id)

    def decode_graph(self, toon_string: str) -> Any:
        """Decode TOON string with circular reference reconstruction.

        Parses a TOON string that contains _graph: true flag and $ref:N
        placeholders. Reconstructs circular references in the resulting
        Python objects.

        Args:
            toon_string: TOON-formatted string to decode.

        Returns:
            Python object (dict, list, or primitive) with circular references.
            Circular structures are properly reconstructed.

        Raises:
            TOONDecodeError: If string cannot be parsed or graph format invalid.

        Examples:
            >>> decoder = GraphDecoder()
            >>> toon = '''_graph: true
            ... a:
            ...   value: 1
            ...   ref: $ref:2
            ... b:
            ...   value: 2
            ...   ref: $ref:1'''
            >>> result = decoder.decode_graph(toon)
            >>> result["a"]["ref"] is result["b"]
            True
            >>> result["b"]["ref"] is result["a"]
            True

            >>> # Regular TOON also works
            >>> result = decoder.decode_graph("_graph: true\\na: 1\\nb: 2")
            >>> result
            {'a': 1, 'b': 2}
        """
        self._object_registry = {}
        self._pending_refs = []

        lines = toon_string.strip().split("\n")

        if not lines:
            return {}

        # Check for _graph: true flag
        first_line = lines[0].strip()
        if first_line != "_graph: true":
            raise TOONDecodeError(
                f"Expected '_graph: true' flag, got: {first_line!r}"
            )

        # Parse the data section (everything after _graph: true)
        data_lines = lines[1:]
        data_string = "\n".join(data_lines).strip()

        if not data_string:
            return {}

        try:
            # First pass: build structure with placeholder markers
            result = self._decode_value(data_string)

            # Second pass: resolve all $ref:N placeholders
            self._resolve_all_references(result)

            return result

        except RecursionError as e:
            raise TOONDecodeError(
                f"Maximum recursion depth exceeded during graph decoding: {e}"
            ) from e
        except TOONDecodeError:
            raise
        except Exception as e:
            raise TOONDecodeError(f"Error during graph decoding: {e}") from e

    def _decode_value(self, value_string: str) -> Any:
        """Decode a TOON value string to Python object.

        Args:
            value_string: TOON value string to decode.

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

        # Check for graph reference placeholder
        ref_match = self._GRAPH_REF_PATTERN.fullmatch(value_string)
        if ref_match:
            ref_id = int(ref_match.group(1))
            # Return placeholder marker that will be resolved later
            return ("__graph_ref__", ref_id)

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
            result: list[Any] = []
            for item in items:
                result.append(self._decode_value(item.strip()))
            return result

        # Check for multiline structure (dict or array)
        if "\n" in value_string:
            return self._decode_multiline(value_string)

        # Check for dict on single line (key: value)
        if ":" in value_string and not value_string.startswith("["):
            return self._decode_dict_lines(value_string.split("\n"))

        # Default: return as string (unquoted)
        return value_string

    def _decode_multiline(self, value_string: str) -> Any:
        """Decode a multiline TOON structure.

        Args:
            value_string: Multiline TOON string.

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
                result: list[Any] = []
                for item in items:
                    result.append(self._decode_value(item.strip()))
                return result

            # List-style array with - prefix
            return self._decode_list_lines(lines[1:], count)

        # It's a dict
        return self._decode_dict_lines(lines)

    def _decode_dict_lines(self, lines: list[str]) -> dict[str, Any]:
        """Decode lines into a dictionary.

        Args:
            lines: Lines representing a dict structure.

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
                result[key] = self._decode_value(value_part)
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
                    result[key] = self._decode_value(nested_str)
                else:
                    result[key] = {}

        return result

    def _decode_list_lines(self, lines: list[str], expected_count: int) -> list[Any]:
        """Decode lines into a list (with - prefix items).

        Args:
            lines: Lines representing list items.
            expected_count: Expected number of items.

        Returns:
            Python list.
        """
        result: list[Any] = []
        i = 0

        # Determine the indentation level of list items
        # Find the first "- " or "-" to establish base indentation
        list_item_indent = -1
        for line in lines:
            if line.strip().startswith("- ") or line.strip() == "-":
                list_item_indent = len(line) - len(line.lstrip())
                break

        if list_item_indent == -1:
            # No list items found
            if expected_count == 0:
                return []
            raise TOONDecodeError(
                f"Array declares {expected_count} items but found 0"
            )

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            current_indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            # Only process items at the correct indentation level
            if current_indent == list_item_indent:
                if stripped.startswith("- "):
                    # Simple item
                    item_value = stripped[2:]
                    result.append(self._decode_value(item_value))
                    i += 1
                elif stripped == "-":
                    # Nested item (multiline)
                    nested_lines = []
                    base_indent = current_indent
                    i += 1

                    while i < len(lines):
                        next_line = lines[i]
                        if not next_line.strip():
                            i += 1
                            continue

                        next_indent = len(next_line) - len(next_line.lstrip())
                        # Stop if we hit another item at same level or less
                        if next_indent <= base_indent:
                            break

                        # Remove the base indentation plus extra indent
                        dedented = next_line[base_indent + 2 :]
                        nested_lines.append(dedented)
                        i += 1

                    if nested_lines:
                        nested_str = "\n".join(nested_lines)
                        result.append(self._decode_value(nested_str))
                    else:
                        result.append({})
                else:
                    i += 1
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

    def _resolve_all_references(self, data: Any) -> None:
        """Resolve all graph reference placeholders.

        Two-pass resolution:
        1. Register all dict/list objects with their assigned IDs
        2. Replace placeholder tuples with actual object references

        Args:
            data: Data structure with potential reference placeholders.
        """
        # First: assign IDs to objects in depth-first order (matching encoder)
        self._assign_ids_from_structure(data)

        # Second: resolve all placeholder tuples
        self._resolve_placeholders(data)

    def _assign_ids_from_structure(self, obj: Any) -> None:
        """Assign IDs to objects based on depth-first traversal order.

        This matches the encoder's ID assignment which uses depth-first
        traversal through _assign_ids().

        Args:
            obj: Object to assign ID to.
        """
        if isinstance(obj, dict):
            python_id = id(obj)
            # Check if we've already assigned an ID to this object
            for assigned_id, registered_obj in self._object_registry.items():
                if registered_obj is obj:
                    return  # Already assigned

            # Assign next ID
            next_id = len(self._object_registry) + 1
            self._object_registry[next_id] = obj

            # Recursively assign IDs to nested objects in order
            for value in obj.values():
                if not isinstance(value, tuple) or len(value) != 2 or value[0] != "__graph_ref__":
                    self._assign_ids_from_structure(value)

        elif isinstance(obj, list):
            python_id = id(obj)
            # Check if we've already assigned an ID to this object
            for assigned_id, registered_obj in self._object_registry.items():
                if registered_obj is obj:
                    return  # Already assigned

            # Assign next ID
            next_id = len(self._object_registry) + 1
            self._object_registry[next_id] = obj

            # Recursively assign IDs to nested objects in order
            for item in obj:
                if not isinstance(item, tuple) or len(item) != 2 or item[0] != "__graph_ref__":
                    self._assign_ids_from_structure(item)

    def _resolve_placeholders(self, obj: Any) -> None:
        """Replace placeholder tuples with actual object references.

        Args:
            obj: Object to resolve placeholders in.
        """
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if isinstance(value, tuple) and len(value) == 2 and value[0] == "__graph_ref__":
                    ref_id = value[1]
                    if ref_id in self._object_registry:
                        obj[key] = self._object_registry[ref_id]
                    else:
                        raise TOONDecodeError(f"Invalid graph reference: $ref:{ref_id}")
                else:
                    self._resolve_placeholders(value)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, tuple) and len(item) == 2 and item[0] == "__graph_ref__":
                    ref_id = item[1]
                    if ref_id in self._object_registry:
                        obj[i] = self._object_registry[ref_id]
                    else:
                        raise TOONDecodeError(f"Invalid graph reference: $ref:{ref_id}")
                else:
                    self._resolve_placeholders(item)
