"""Core TOON decoder with depth-based parsing.

Implements proper indentation tracking per TOON v2.0 specification,
enabling correct parsing of nested objects within list-format arrays.
"""

from __future__ import annotations

from typing import Any

from pytoon.decoder.parser_utils import (
    parse_array_header,
    parse_delimited_values,
    parse_key_token,
    parse_primitive_token,
)
from pytoon.decoder.scanner import LineCursor, scan_lines
from pytoon.decoder.types import ArrayHeaderInfo
from pytoon.utils.errors import TOONDecodeError, TOONValidationError

LIST_ITEM_PREFIX = "- "


def decode_toon(source: str, indent_size: int = 2, strict: bool = True) -> Any:
    """Decode TOON source to Python object.

    Uses depth-based parsing to properly handle nested structures
    including objects within list-format arrays.

    Args:
        source: TOON source string
        indent_size: Spaces per indentation level (default 2)
        strict: Enable strict validation (default True)

    Returns:
        Decoded Python value (dict, list, or primitive)

    Raises:
        TOONDecodeError: For malformed input
        TOONValidationError: For validation failures in strict mode

    Examples:
        >>> decode_toon("name: Alice\\nage: 30")
        {'name': 'Alice', 'age': 30}
        >>> decode_toon("[2]:\\n  - 1\\n  - 2")
        [1, 2]
    """
    scan_result = scan_lines(source, indent_size, strict)

    if not scan_result.lines:
        return {}  # Empty document → empty object

    cursor = LineCursor(scan_result.lines, scan_result.blank_lines)
    return decode_value_from_cursor(cursor, indent_size, strict)


def decode_value_from_cursor(
    cursor: LineCursor, indent_size: int, strict: bool
) -> Any:
    """Decode value starting from cursor position.

    Determines the type of root value and dispatches to appropriate decoder.

    Args:
        cursor: Line cursor positioned at start
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Decoded Python value

    Raises:
        TOONDecodeError: If no content to decode
    """
    first = cursor.peek()
    if not first:
        raise TOONDecodeError("No content to decode")

    # Check for root array header
    header_result = parse_array_header(first.content)
    if header_result and not header_result[0].key:
        cursor.advance()
        return decode_array_from_header(
            header_result[0], header_result[1], cursor, 0, indent_size, strict
        )

    # Check for single primitive (one line, no colon)
    if len(cursor._lines) == 1 and ":" not in first.content:
        return parse_primitive_token(first.content.strip())

    # Default to object
    return decode_object(cursor, 0, indent_size, strict)


def decode_object(
    cursor: LineCursor, base_depth: int, indent_size: int, strict: bool
) -> dict[str, Any]:
    """Decode an object at given depth.

    Reads key-value pairs at the computed depth level.

    Args:
        cursor: Line cursor
        base_depth: Expected depth of object fields
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Decoded dictionary
    """
    obj: dict[str, Any] = {}
    computed_depth: int | None = None

    while not cursor.at_end():
        line = cursor.peek()
        if not line or line.depth < base_depth:
            break

        # Compute actual field depth from first field
        if computed_depth is None and line.depth >= base_depth:
            computed_depth = line.depth

        if line.depth == computed_depth:
            cursor.advance()
            key, value = decode_key_value(
                line.content, cursor, computed_depth, indent_size, strict
            )
            if strict and key in obj:
                raise TOONDecodeError(
                    f"Duplicate key {key!r} at line {line.line_number}"
                )
            obj[key] = value
        else:
            # Different depth - stop object parsing
            break

    return obj


def decode_key_value(
    content: str,
    cursor: LineCursor,
    base_depth: int,
    indent_size: int,
    strict: bool,
) -> tuple[str, Any]:
    """Decode a key-value pair from line content.

    Handles:
    - Array headers: `key[N]{fields}: ...`
    - Nested objects: `key:` (empty value, nested structure below)
    - Inline primitives: `key: value`

    Args:
        content: Line content (after indentation)
        cursor: Line cursor for reading nested structures
        base_depth: Current nesting depth
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Tuple of (key, value)
    """
    # Check for array header (key with [N])
    header_result = parse_array_header(content)
    if header_result and header_result[0].key:
        value = decode_array_from_header(
            header_result[0],
            header_result[1],
            cursor,
            base_depth,
            indent_size,
            strict,
        )
        return header_result[0].key, value

    # Regular key-value pair
    key, after_colon, _ = parse_key_token(content, 0)
    rest = content[after_colon:].strip()

    if not rest:
        # No value after colon → nested object, nested array, or empty string
        next_line = cursor.peek()
        if next_line and next_line.depth > base_depth:
            # Check if nested value is an anonymous array header
            nested_header = parse_array_header(next_line.content)
            if nested_header and not nested_header[0].key:
                # Anonymous array as value (e.g., key:\n  [N]:)
                cursor.advance()
                value = decode_array_from_header(
                    nested_header[0],
                    nested_header[1],
                    cursor,
                    base_depth + 1,
                    indent_size,
                    strict,
                )
                return key, value
            # Otherwise nested object
            nested = decode_object(cursor, base_depth + 1, indent_size, strict)
            return key, nested
        # Empty string (no nested content)
        return key, ""

    # Check if the rest is an inline array header (e.g., "[0]:" or "[3]: 1,2,3")
    inline_array_header = parse_array_header(rest)
    if inline_array_header and not inline_array_header[0].key:
        # This is an anonymous array as inline value
        value = decode_array_from_header(
            inline_array_header[0],
            inline_array_header[1],
            cursor,
            base_depth,
            indent_size,
            strict,
        )
        return key, value

    # Inline primitive value
    value = parse_primitive_token(rest)
    return key, value


def decode_array_from_header(
    header: ArrayHeaderInfo,
    inline_values: str | None,
    cursor: LineCursor,
    base_depth: int,
    indent_size: int,
    strict: bool,
) -> list[Any]:
    """Decode array based on header information.

    Dispatches to appropriate array decoder based on header type.

    Args:
        header: Parsed header info
        inline_values: Values after colon (if inline array)
        cursor: Line cursor
        base_depth: Array depth
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Decoded list
    """
    # Inline primitive array
    if inline_values:
        return decode_inline_array(header, inline_values, strict)

    # Tabular array (has fields)
    if header.fields:
        return decode_tabular_array(header, cursor, base_depth, indent_size, strict)

    # List array
    return decode_list_array(header, cursor, base_depth, indent_size, strict)


def decode_inline_array(
    header: ArrayHeaderInfo, values_str: str, strict: bool
) -> list[Any]:
    """Decode inline primitive array.

    Args:
        header: Array header info
        values_str: Delimiter-separated values
        strict: Strict mode flag

    Returns:
        List of primitives

    Raises:
        TOONValidationError: If count mismatch in strict mode
    """
    if not values_str.strip():
        if strict and header.length != 0:
            raise TOONValidationError(
                f"Array declares {header.length} items but found 0"
            )
        return []

    # Auto-detect delimiter if the header's delimiter doesn't work
    # This supports legacy format where delimiter isn't specified in header
    delimiter = header.delimiter
    if delimiter == "," and "," not in values_str:
        # Try auto-detecting: tab first, then pipe
        if "\t" in values_str:
            delimiter = "\t"
        elif "|" in values_str:
            delimiter = "|"

    values = parse_delimited_values(values_str, delimiter)
    primitives = [parse_primitive_token(v) for v in values]

    if strict and len(primitives) != header.length:
        raise TOONValidationError(
            f"Array declares {header.length} items but found {len(primitives)}"
        )

    return primitives


def decode_tabular_array(
    header: ArrayHeaderInfo,
    cursor: LineCursor,
    base_depth: int,
    indent_size: int,
    strict: bool,
) -> list[dict[str, Any]]:
    """Decode tabular array (uniform objects).

    Args:
        header: Array header with fields
        cursor: Line cursor
        base_depth: Array depth
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        List of dictionaries

    Raises:
        TOONValidationError: For validation errors in strict mode
    """
    objects: list[dict[str, Any]] = []
    row_depth: int | None = None

    while not cursor.at_end() and len(objects) < header.length:
        line = cursor.peek()
        if not line:
            break

        # Determine expected row depth from first row
        if row_depth is None:
            # Rows can be at base_depth (root array) or base_depth + 1 (nested)
            if line.depth >= base_depth:
                row_depth = line.depth
            else:
                break

        if line.depth < row_depth:
            break

        if line.depth == row_depth:
            cursor.advance()
            values = parse_delimited_values(line.content, header.delimiter)

            if strict and header.fields and len(values) != len(header.fields):
                raise TOONValidationError(
                    f"Row has {len(values)} values but expected "
                    f"{len(header.fields)} fields at line {line.line_number}"
                )

            primitives = [parse_primitive_token(v) for v in values]
            obj: dict[str, Any] = {}
            for i, field in enumerate(header.fields or []):
                if i < len(primitives):
                    obj[field] = primitives[i]
            objects.append(obj)
        else:
            break

    if strict and len(objects) != header.length:
        raise TOONValidationError(
            f"Array declares {header.length} rows but found {len(objects)}"
        )

    return objects


def decode_list_array(
    header: ArrayHeaderInfo,
    cursor: LineCursor,
    base_depth: int,
    indent_size: int,
    strict: bool,
) -> list[Any]:
    """Decode list-format array.

    Args:
        header: Array header
        cursor: Line cursor
        base_depth: Array depth
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        List of values

    Raises:
        TOONValidationError: For validation errors in strict mode
    """
    items: list[Any] = []
    item_depth: int | None = None

    while not cursor.at_end() and len(items) < header.length:
        line = cursor.peek()
        if not line:
            break

        # Check for list item marker
        is_list_item = line.content.startswith(LIST_ITEM_PREFIX) or line.content == "-"

        # Determine expected item depth from first item
        if item_depth is None and is_list_item:
            # Items can be at base_depth (root array) or base_depth + 1 (nested)
            if line.depth >= base_depth:
                item_depth = line.depth
            else:
                break

        if item_depth is not None and line.depth < item_depth:
            break

        if item_depth is not None and line.depth == item_depth and is_list_item:
            item = decode_list_item(cursor, item_depth, indent_size, strict)
            items.append(item)
        else:
            break

    if strict and len(items) != header.length:
        raise TOONValidationError(
            f"Array declares {header.length} items but found {len(items)}"
        )

    return items


def decode_list_item(
    cursor: LineCursor, base_depth: int, indent_size: int, strict: bool
) -> Any:
    """Decode a single list item.

    Handles:
    - Empty items: `- ` → {}
    - Primitives: `- value`
    - Nested arrays: `- [N]: ...`
    - Objects: `- key: value` (first field on hyphen line)

    Args:
        cursor: Line cursor
        base_depth: List item depth
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Decoded item value

    Raises:
        TOONDecodeError: If list item format is invalid
    """
    line = cursor.next()
    if not line:
        raise TOONDecodeError("Expected list item")

    # Extract content after "- "
    if line.content == "-":
        # Empty list item → empty object
        return {}
    elif line.content.startswith(LIST_ITEM_PREFIX):
        after_hyphen = line.content[len(LIST_ITEM_PREFIX) :]
    else:
        raise TOONDecodeError(
            f"Expected list item to start with '{LIST_ITEM_PREFIX}' "
            f"at line {line.line_number}"
        )

    if not after_hyphen.strip():
        # Empty content after hyphen → empty object
        return {}

    # Check for nested array header (- [N]: ...)
    header_result = parse_array_header(after_hyphen)
    if header_result:
        return decode_array_from_header(
            header_result[0],
            header_result[1],
            cursor,
            base_depth,
            indent_size,
            strict,
        )

    # Check for object (has colon → first field on hyphen line)
    if ":" in after_hyphen:
        return decode_object_from_list_item(
            after_hyphen, cursor, base_depth, indent_size, strict
        )

    # Primitive value
    return parse_primitive_token(after_hyphen)


def decode_object_from_list_item(
    first_field_content: str,
    cursor: LineCursor,
    base_depth: int,
    indent_size: int,
    strict: bool,
) -> dict[str, Any]:
    """Decode an object that starts as a list item.

    Per TOON v2.0 §10:
    - First field is on the hyphen line (after "- ")
    - Subsequent sibling fields are at base_depth + 1
    - Nested objects have fields at base_depth + 2

    Args:
        first_field_content: Content after "- " on hyphen line
        cursor: Line cursor
        base_depth: List item depth (depth of the "- " line)
        indent_size: Indentation size
        strict: Strict mode flag

    Returns:
        Decoded dictionary

    Examples:
        Input TOON:
            - id: 1
              meta:
                created: 2025
              status: active

        Result: {'id': 1, 'meta': {'created': 2025}, 'status': 'active'}
    """
    # Parse first field (on hyphen line)
    key, value = decode_key_value(
        first_field_content, cursor, base_depth, indent_size, strict
    )
    obj: dict[str, Any] = {key: value}

    # Determine follow depth for sibling fields
    # This is base_depth + 1 (one level deeper than the hyphen line's depth)
    follow_depth = base_depth + 1

    # Read subsequent fields at follow_depth
    while not cursor.at_end():
        line = cursor.peek()
        if not line or line.depth < follow_depth:
            break

        # Check if this is a sibling field at the expected depth
        if line.depth == follow_depth and not line.content.startswith(LIST_ITEM_PREFIX):
            cursor.advance()
            k, v = decode_key_value(
                line.content, cursor, follow_depth, indent_size, strict
            )
            if strict and k in obj:
                raise TOONDecodeError(
                    f"Duplicate key {k!r} at line {line.line_number}"
                )
            obj[k] = v
        else:
            # Different depth or new list item → stop
            break

    return obj
