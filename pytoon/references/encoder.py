"""Reference encoder with object identity tracking and schema generation.

This module provides reference detection capabilities for PyToon, enabling
encoding of relational data with shared object references and schema metadata.

Key Components:
    - ReferenceInfo: Dataclass containing detected reference information
    - ReferenceEncoder: Encoder that tracks shared objects and generates schemas
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pytoon.utils.errors import TOONDecodeError, TOONEncodeError


@dataclass
class ReferenceInfo:
    """Container for detected reference information.

    Stores information about shared object references discovered during
    data traversal, including object ID mappings, occurrence counts,
    and generated schema metadata.

    Attributes:
        shared_objects: Maps Python id() to (object, count, assigned_id).
            The assigned_id is a string like "$1", "$2", etc.
        reference_fields: Set of field names that are reference fields
            (ending in "Id" or "Ref").
        schema: Dictionary mapping type names to their field definitions.
            Format: {"TypeName": {"field1": type_str, "field2": type_str}}
        object_count: Total number of objects traversed.

    Examples:
        >>> info = ReferenceInfo()
        >>> info.shared_objects[12345] = ({"id": 1}, 2, "$1")
        >>> info.reference_fields.add("userId")
        >>> info.schema["User"] = {"id": "int", "name": "str"}
    """

    shared_objects: dict[int, tuple[Any, int, str]] = field(default_factory=dict)
    reference_fields: set[str] = field(default_factory=set)
    schema: dict[str, dict[str, str]] = field(default_factory=dict)
    object_count: int = 0


class ReferenceEncoder:
    """Encoder that detects shared object references and generates schemas.

    Tracks objects by Python id() during traversal to detect when the same
    object is referenced multiple times. Identifies reference fields by
    naming patterns (*Id, *Ref) and generates schema metadata for shared types.

    The reference detection is O(n) where n is the total number of objects
    in the data structure, using a hash map for id() tracking.

    Examples:
        >>> encoder = ReferenceEncoder()
        >>> user = {"id": 1, "name": "Alice"}
        >>> data = {"users": [user], "admins": [user]}
        >>> info = encoder.detect_references(data)
        >>> len(info.shared_objects)
        1
        >>> "$1" in [v[2] for v in info.shared_objects.values()]
        True

        >>> info = encoder.detect_references({"userId": 1, "authorRef": "Alice"})
        >>> "userId" in info.reference_fields
        True
        >>> "authorRef" in info.reference_fields
        True
    """

    # Pattern to match reference field names (userId, authorRef, etc.)
    _REFERENCE_PATTERN: re.Pattern[str] = re.compile(r"^.+(Id|Ref)$")

    def __init__(self) -> None:
        """Initialize the ReferenceEncoder.

        Creates a new encoder instance for detecting object references.
        """
        self._id_counter: int = 0

    def detect_references(self, data: Any) -> ReferenceInfo:
        """Detect shared object references in data.

        Traverses the data structure, tracking objects by their Python id()
        to identify shared references. Also identifies reference fields and
        generates schema metadata for shared object types.

        Args:
            data: Python object to analyze (dict, list, or any structure).

        Returns:
            ReferenceInfo containing detected references, fields, and schema.

        Raises:
            TOONEncodeError: If an error occurs during reference detection.

        Examples:
            >>> encoder = ReferenceEncoder()
            >>> user = {"id": 1, "name": "Alice"}
            >>> data = {"users": [user], "admins": [user]}
            >>> info = encoder.detect_references(data)
            >>> info.object_count > 0
            True
            >>> len(info.shared_objects) == 1
            True
        """
        self._id_counter = 0
        info = ReferenceInfo()
        seen: dict[int, tuple[Any, int]] = {}  # id -> (object, count)

        try:
            self._traverse_and_detect(data, seen, info)

            # Filter to only shared objects (count > 1) and assign IDs
            for obj_id, (obj, count) in seen.items():
                if count > 1 and isinstance(obj, dict):
                    self._id_counter += 1
                    assigned_id = f"${self._id_counter}"
                    info.shared_objects[obj_id] = (obj, count, assigned_id)

            # Generate schema for shared objects
            info.schema = self._generate_schema(info.shared_objects)

        except RecursionError as e:
            raise TOONEncodeError(
                f"Maximum recursion depth exceeded during reference detection: {e}"
            ) from e
        except Exception as e:
            raise TOONEncodeError(
                f"Error during reference detection: {e}"
            ) from e

        return info

    def _traverse_and_detect(
        self,
        obj: Any,
        seen: dict[int, tuple[Any, int]],
        info: ReferenceInfo,
    ) -> None:
        """Recursively traverse data structure and track object occurrences.

        Performs depth-first traversal of the data, tracking each object
        by its Python id() and counting occurrences. Also identifies
        reference fields by naming patterns.

        Args:
            obj: Current object being traversed.
            seen: Dictionary mapping id() to (object, count).
            info: ReferenceInfo to update with findings.
        """
        # Only track dict and list objects (compound types)
        if isinstance(obj, dict):
            obj_id = id(obj)

            # Check if already seen
            if obj_id in seen:
                # Increment count for shared reference
                prev_obj, prev_count = seen[obj_id]
                seen[obj_id] = (prev_obj, prev_count + 1)
                # Don't recurse into already-seen objects to avoid infinite loops
                return

            # First time seeing this object
            seen[obj_id] = (obj, 1)
            info.object_count += 1

            # Identify reference fields and recurse into values
            for key, value in obj.items():
                # Check if key matches reference pattern
                ref_fields = self._identify_reference_fields(key)
                info.reference_fields.update(ref_fields)

                # Recurse into value
                self._traverse_and_detect(value, seen, info)

        elif isinstance(obj, list):
            obj_id = id(obj)

            # Check if already seen
            if obj_id in seen:
                prev_obj, prev_count = seen[obj_id]
                seen[obj_id] = (prev_obj, prev_count + 1)
                return

            # First time seeing this list
            seen[obj_id] = (obj, 1)
            info.object_count += 1

            # Recurse into list elements
            for item in obj:
                self._traverse_and_detect(item, seen, info)

        # Primitives (int, str, float, bool, None) are not tracked by id()
        # as they may be interned by Python

    def _identify_reference_fields(self, key: str) -> set[str]:
        """Identify if a field name indicates a reference.

        Checks if the field name ends with "Id" or "Ref", which are
        conventional patterns for reference fields in relational data.

        Args:
            key: Field name to check.

        Returns:
            Set containing the key if it matches reference pattern, empty otherwise.

        Examples:
            >>> encoder = ReferenceEncoder()
            >>> encoder._identify_reference_fields("userId")
            {'userId'}
            >>> encoder._identify_reference_fields("authorRef")
            {'authorRef'}
            >>> encoder._identify_reference_fields("name")
            set()
            >>> encoder._identify_reference_fields("id")
            set()
        """
        if not isinstance(key, str):
            return set()

        if self._REFERENCE_PATTERN.match(key):
            return {key}

        return set()

    def _generate_schema(
        self,
        shared_objects: dict[int, tuple[Any, int, str]],
    ) -> dict[str, dict[str, str]]:
        """Generate schema metadata for shared object types.

        Analyzes shared objects and creates type definitions based on their
        structure. Types are inferred from object fields and their values.

        Args:
            shared_objects: Dictionary mapping id() to (object, count, assigned_id).

        Returns:
            Dictionary mapping type names to field type definitions.
            Format: {"TypeName": {"field1": "type", "field2": "type"}}

        Examples:
            >>> encoder = ReferenceEncoder()
            >>> obj = {"id": 1, "name": "Alice", "active": True}
            >>> shared = {id(obj): (obj, 2, "$1")}
            >>> schema = encoder._generate_schema(shared)
            >>> "Object1" in schema
            True
            >>> schema["Object1"]["id"]
            'int'
            >>> schema["Object1"]["name"]
            'str'
            >>> schema["Object1"]["active"]
            'bool'
        """
        schema: dict[str, dict[str, str]] = {}
        type_counter = 0

        for _obj_id, (obj, _count, _assigned_id) in shared_objects.items():
            if isinstance(obj, dict):
                type_counter += 1
                type_name = f"Object{type_counter}"
                field_types: dict[str, str] = {}

                for field_name, field_value in obj.items():
                    field_types[str(field_name)] = self._infer_type(field_value)

                schema[type_name] = field_types

        return schema

    def _infer_type(self, value: Any) -> str:
        """Infer the type string for a value.

        Returns a string representation of the value's type for schema
        generation. Handles primitive types, lists, dicts, and None.

        Args:
            value: Value to infer type for.

        Returns:
            String representation of the type (e.g., "int", "str", "list", "dict").

        Examples:
            >>> encoder = ReferenceEncoder()
            >>> encoder._infer_type(42)
            'int'
            >>> encoder._infer_type("hello")
            'str'
            >>> encoder._infer_type(3.14)
            'float'
            >>> encoder._infer_type(True)
            'bool'
            >>> encoder._infer_type(None)
            'null'
            >>> encoder._infer_type([1, 2, 3])
            'list'
            >>> encoder._infer_type({"a": 1})
            'dict'
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            # Check bool before int since bool is subclass of int
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "dict"

        # Fallback for other types
        return type(value).__name__

    def encode_refs(
        self,
        data: Any,
        mode: str = "schema",
        *,
        indent: int = 2,
        delimiter: str = ",",
    ) -> str:
        """Encode data with reference tracking using schema-based format.

        Detects shared object references in the data and encodes them using
        placeholders ($1, $2, etc.) with a schema section describing the
        shared types. This enables efficient encoding of relational data.

        Args:
            data: Python object to encode (dict, list, or primitive).
            mode: Encoding mode - currently only 'schema' is supported.
            indent: Number of spaces per indentation level (default: 2).
            delimiter: Field delimiter for tabular arrays (default: ',').

        Returns:
            TOON-formatted string with _schema section and reference placeholders.

        Raises:
            TOONEncodeError: If mode is invalid or encoding fails.
            ValueError: If configuration parameters are invalid.

        Examples:
            >>> encoder = ReferenceEncoder()
            >>> user = {"id": 1, "name": "Alice"}
            >>> data = {"users": [user], "admins": [user]}
            >>> result = encoder.encode_refs(data)
            >>> "_schema:" in result
            True
            >>> "$1" in result
            True

            >>> # Simple case with no shared references
            >>> data = {"a": 1, "b": 2}
            >>> result = encoder.encode_refs(data)
            >>> "_schema:" not in result  # No schema if no shared refs
            True
        """
        if mode != "schema":
            raise TOONEncodeError(f"Unsupported encoding mode: {mode!r}")

        # Detect shared references
        info = self.detect_references(data)

        # If no shared objects, encode without schema
        if not info.shared_objects:
            return self._encode_value_simple(data, 0, {}, indent, delimiter)

        # Build schema section
        schema_lines: list[str] = ["_schema:"]
        for type_name, fields in info.schema.items():
            schema_lines.append(f"{' ' * indent}{type_name}:")
            for field_name, field_type in fields.items():
                schema_lines.append(f"{' ' * (indent * 2)}{field_name}: {field_type}")

        # Build reverse mapping: object_id -> assigned_id
        obj_id_to_ref: dict[int, str] = {
            obj_id: assigned_id
            for obj_id, (_obj, _count, assigned_id) in info.shared_objects.items()
        }

        # Encode data with references
        data_encoded = self._encode_value_with_refs(
            data, 0, obj_id_to_ref, indent, delimiter
        )

        # Combine schema and data
        return "\n".join(schema_lines) + "\n" + data_encoded

    def _encode_value_simple(
        self,
        value: Any,
        depth: int,
        obj_id_to_ref: dict[int, str],
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a value without reference substitution.

        Args:
            value: Value to encode.
            depth: Current nesting depth.
            obj_id_to_ref: Mapping from object id() to reference string.
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
            return self._encode_string_value(value)
        if isinstance(value, list):
            return self._encode_list_with_refs(value, depth, obj_id_to_ref, indent, delimiter)
        if isinstance(value, dict):
            return self._encode_dict_with_refs(value, depth, obj_id_to_ref, indent, delimiter)

        raise TOONEncodeError(f"Cannot encode type: {type(value)}")

    def _encode_value_with_refs(
        self,
        value: Any,
        depth: int,
        obj_id_to_ref: dict[int, str],
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a value, substituting shared objects with references.

        Args:
            value: Value to encode.
            depth: Current nesting depth.
            obj_id_to_ref: Mapping from object id() to reference string.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted string with reference placeholders.
        """
        # Check if this object should be replaced with a reference
        if isinstance(value, dict) and id(value) in obj_id_to_ref:
            return obj_id_to_ref[id(value)]

        return self._encode_value_simple(value, depth, obj_id_to_ref, indent, delimiter)

    def _encode_string_value(self, value: str) -> str:
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

    def _encode_list_with_refs(
        self,
        value: list[Any],
        depth: int,
        obj_id_to_ref: dict[int, str],
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a list with reference substitution.

        Args:
            value: List to encode.
            depth: Current nesting depth.
            obj_id_to_ref: Mapping from object id() to reference string.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted array string.
        """
        if not value:
            return "[0]:"

        # Check if all items are primitives or references
        all_simple = all(
            isinstance(item, (type(None), bool, int, float, str))
            or (isinstance(item, dict) and id(item) in obj_id_to_ref)
            for item in value
        )

        if all_simple:
            encoded_items = [
                self._encode_value_with_refs(item, depth + 1, obj_id_to_ref, indent, delimiter)
                for item in value
            ]
            return f"[{len(value)}]: {delimiter.join(encoded_items)}"

        # Fall back to list format
        indent_str = " " * indent
        lines = [f"[{len(value)}]:"]
        for item in value:
            encoded = self._encode_value_with_refs(
                item, depth + 1, obj_id_to_ref, indent, delimiter
            )
            if "\n" in encoded:
                lines.append(f"{indent_str}-")
                for line in encoded.split("\n"):
                    lines.append(f"{indent_str}{indent_str}{line}")
            else:
                lines.append(f"{indent_str}- {encoded}")
        return "\n".join(lines)

    def _encode_dict_with_refs(
        self,
        value: dict[str, Any],
        depth: int,
        obj_id_to_ref: dict[int, str],
        indent: int,
        delimiter: str,
    ) -> str:
        """Encode a dictionary with reference substitution.

        Args:
            value: Dictionary to encode.
            depth: Current nesting depth.
            obj_id_to_ref: Mapping from object id() to reference string.
            indent: Indentation size.
            delimiter: Field delimiter.

        Returns:
            TOON-formatted object string.
        """
        if not value:
            return ""

        lines: list[str] = []
        indent_str = " " * (indent * depth)

        for key, val in value.items():
            if not isinstance(key, str):
                raise TOONEncodeError(f"Dictionary keys must be strings, got: {type(key)}")

            encoded_val = self._encode_value_with_refs(
                val, depth + 1, obj_id_to_ref, indent, delimiter
            )

            if "\n" in encoded_val:
                lines.append(f"{indent_str}{key}:")
                for line in encoded_val.split("\n"):
                    lines.append(f"{indent_str}{' ' * indent}{line}")
            else:
                lines.append(f"{indent_str}{key}: {encoded_val}")

        return "\n".join(lines)
