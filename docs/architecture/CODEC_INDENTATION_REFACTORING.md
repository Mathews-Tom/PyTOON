# PyToon Codec Indentation Tracking Refactoring

## Executive Summary

The core PyToon **encoder and decoder** have **critical architectural limitations** that prevent proper handling of nested objects within list-format arrays:

1. **Encoder Bug**: Incorrectly formats objects in list items by placing entire encoded value after `"- "` instead of first field on hyphen line (violates TOON v2.0 §10)

2. **Decoder Bug**: Strips indentation information during parsing and relies on pattern matching (`"- "` prefix) instead of depth-based parsing

This document provides a comprehensive refactoring strategy for **both encoder and decoder** based on analysis of the official TOON v2.0 specification and the reference TypeScript implementation.

**Severity**: CRITICAL
**Impact**: Nested objects in list-format arrays fail to roundtrip correctly
**Effort**: Major refactor (estimated 3-5 days)
**Scope**: Both encoder and decoder require fixes

---

## 1. Problem Analysis

### 1.1 Root Cause

The current decoder in `pytoon/core/decoder.py` at line 361 does this:

```python
def _parse_list_array(self, data_lines: list[str], declared_length: int) -> list[Any]:
    for line in data_lines:
        stripped = line.strip()  # ← CRITICAL BUG: Loses ALL indentation information!
        if stripped.startswith("- "):
            # Detect new item by pattern match only
```

This approach:

1. **Destroys indentation context** - Cannot distinguish depth levels
2. **Uses heuristic pattern matching** - Fails when content contains `"- "` patterns
3. **Cannot handle nested structures** - No way to know when nested object ends vs. sibling field continues

### 1.2 Manifestation

Input data:

```python
data = [
    {'id': 1, 'meta': {'created': '2025'}},
    {'id': 2, 'meta': {'created': '2024'}},
]
```

Expected TOON encoding:

```toon
[2]:
  - id: 1
    meta:
      created: "2025"
  - id: 2
    meta:
      created: "2024"
```

Current encoder output (WRONG):

```toon
[2]:
  -   id: 1
  meta:     created: "2025"    # ← Malformed: wrong indentation, no nesting
  -   id: 2
  meta:     created: "2024"
```

Decoded result (WRONG):

```python
[{'id': 1, 'meta': 'created: "2025"'}, ...]  # meta is STRING, not dict!
```

### 1.3 Encoder Contribution to Problem

The encoder at `pytoon/core/encoder.py:286` also has issues:

```python
def _encode_list(self, value: list[Any], depth: int) -> str:
    for item in value:
        encoded = self._encode_value(item, depth + 1)
        lines.append(f"{indent}- {encoded}")  # ← Appends ENTIRE encoded value after "- "
```

This incorrectly places multi-line values after the hyphen marker, instead of placing the first field on the hyphen line as required by TOON v2.0 spec §10.

---

## 2. TOON v2.0 Specification Requirements

### 2.1 Objects as List Items (§10)

From the official TOON v2.0 specification:

> For an object appearing as a list item:
>
> - **First field on the hyphen line**: `- key: value`
> - **Remaining fields** appear at depth +1 under the hyphen line
> - If first field is a nested object (`- key:`), nested fields are at depth +2 relative to hyphen line

Example:

```toon
items[2]:
  - id: 1           # First field on hyphen line (depth 1)
    name: First     # Subsequent field at depth 1 (sibling)
  - id: 2
    name: Second
    extra: true
```

Nested object in list item:

```toon
items[1]:
  - meta:           # First field on hyphen line, starts nested object
      created: 2025 # Nested at depth +2 relative to hyphen
    status: active  # Sibling field at depth +1 relative to hyphen
```

### 2.2 Indentation Rules (§12)

> - Encoders MUST use consistent number of spaces per level (default 2)
> - Decoders MUST track indentation to determine structure depth
> - Strict mode: leading spaces MUST be exact multiple of indentSize
> - Tabs MUST NOT be used for indentation

### 2.3 Depth-Based Parsing

The specification mandates depth-based structure detection:

- **Objects**: Lines at same depth are sibling fields; deeper lines are nested values
- **List items**: Start with `"- "` at itemDepth; content is at various depths relative to hyphen
- **Arrays**: Items/rows appear at baseDepth + 1

---

## 3. Reference Implementation Analysis

### 3.1 TypeScript Reference Architecture

The official TOON TypeScript implementation uses:

1. **Scanner** (`packages/toon/src/decode/scanner.ts`):

   ```typescript
   export function toParsedLines(source: string, indentSize: number, strict: boolean): ScanResult {
     // Pre-compute depth for every line
     const depth = Math.floor(indentSpaces / indentSize)
     parsed.push({ raw, indent, content, depth, lineNumber })
   }

   export class LineCursor {
     peek(): ParsedLine | undefined
     next(): ParsedLine | undefined
     peekAtDepth(targetDepth: Depth): ParsedLine | undefined
   }
   ```

2. **Depth-Based Decoding** (`packages/toon/src/decode/decoders.ts`):

   ```typescript
   function decodeObjectFromListItem(firstLine, cursor, baseDepth, options) {
     const { key, value, followDepth } = decodeKeyValue(afterHyphen, cursor, baseDepth, options)
     const obj = { [key]: value }

     // Read subsequent fields at SAME depth (followDepth)
     while (!cursor.atEnd()) {
       const line = cursor.peek()
       if (line.depth === followDepth && !line.content.startsWith('-')) {
         cursor.advance()
         const { key: k, value: v } = decodeKeyValue(line.content, cursor, followDepth, options)
         obj[k] = v
       } else {
         break  // Different depth or new list item
       }
     }
     return obj
   }
   ```

3. **Key-Value Decoding with Nesting Detection**:

   ```typescript
   function decodeKeyValue(content, cursor, baseDepth, options) {
     const rest = content.slice(colonEnd).trim()

     if (!rest) {  // No value after colon → nested object
       const nextLine = cursor.peek()
       if (nextLine && nextLine.depth > baseDepth) {
         const nested = decodeObject(cursor, baseDepth + 1, options)
         return { key, value: nested, followDepth: baseDepth + 1 }
       }
       return { key, value: {}, followDepth: baseDepth + 1 }  // Empty object
     }

     return { key, value: parsePrimitive(rest), followDepth: baseDepth + 1 }
   }
   ```

### 3.2 Key Design Principles

1. **Pre-scan with depth computation**: Parse all lines upfront, compute depth from indentation
2. **Cursor-based navigation**: Use a cursor to track position and peek ahead
3. **followDepth tracking**: Know where sibling fields should appear after parsing a value
4. **Depth comparison for structure**: Compare depths to determine parent-child-sibling relationships
5. **Recursive descent**: Parse nested structures by recursively calling parsers with deeper base depths

---

## 4. Refactoring Strategy

### 4.1 Phase 1: Data Structures

Create new types for parsed lines with depth tracking:

```python
# pytoon/decoder/types.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ParsedLine:
    """A single parsed line with computed metadata."""
    raw: str           # Original line text
    indent: int        # Number of leading spaces
    content: str       # Content after indentation
    depth: int         # Computed depth (indent // indent_size)
    line_number: int   # 1-based line number for errors

@dataclass
class BlankLineInfo:
    """Track blank lines for validation."""
    line_number: int
    indent: int
    depth: int

@dataclass
class ArrayHeaderInfo:
    """Parsed array header information."""
    key: str | None
    length: int
    delimiter: str
    fields: list[str] | None
```

### 4.2 Phase 2: Scanner/Tokenizer

Implement a line scanner that pre-processes input:

```python
# pytoon/decoder/scanner.py

from __future__ import annotations
from pytoon.decoder.types import ParsedLine, BlankLineInfo
from pytoon.utils.errors import TOONDecodeError

class ScanResult:
    """Result of scanning TOON input."""
    def __init__(self, lines: list[ParsedLine], blank_lines: list[BlankLineInfo]) -> None:
        self.lines = lines
        self.blank_lines = blank_lines

class LineCursor:
    """Cursor for navigating parsed lines."""

    def __init__(self, lines: list[ParsedLine], blank_lines: list[BlankLineInfo] | None = None) -> None:
        self._lines = lines
        self._index = 0
        self._blank_lines = blank_lines or []

    def peek(self) -> ParsedLine | None:
        """Look at current line without advancing."""
        if self._index < len(self._lines):
            return self._lines[self._index]
        return None

    def next(self) -> ParsedLine | None:
        """Get current line and advance cursor."""
        if self._index < len(self._lines):
            line = self._lines[self._index]
            self._index += 1
            return line
        return None

    def current(self) -> ParsedLine | None:
        """Get the last consumed line."""
        if self._index > 0:
            return self._lines[self._index - 1]
        return None

    def advance(self) -> None:
        """Move cursor forward."""
        self._index += 1

    def at_end(self) -> bool:
        """Check if cursor is at end."""
        return self._index >= len(self._lines)

    def peek_at_depth(self, target_depth: int) -> ParsedLine | None:
        """Peek if next line matches target depth."""
        line = self.peek()
        if line and line.depth == target_depth:
            return line
        return None

    @property
    def blank_lines(self) -> list[BlankLineInfo]:
        """Get tracked blank lines."""
        return self._blank_lines

def scan_lines(source: str, indent_size: int, strict: bool) -> ScanResult:
    """Scan TOON source into parsed lines with depth computation.

    Args:
        source: TOON source string
        indent_size: Number of spaces per indentation level
        strict: Enable strict validation

    Returns:
        ScanResult with parsed lines and blank line tracking

    Raises:
        TOONDecodeError: If indentation is invalid in strict mode
    """
    if not source.strip():
        return ScanResult([], [])

    raw_lines = source.split('\n')
    parsed: list[ParsedLine] = []
    blank_lines: list[BlankLineInfo] = []

    for i, raw in enumerate(raw_lines):
        line_number = i + 1

        # Count leading spaces
        indent = 0
        while indent < len(raw) and raw[indent] == ' ':
            indent += 1

        content = raw[indent:]

        # Track blank lines separately
        if not content.strip():
            depth = indent // indent_size
            blank_lines.append(BlankLineInfo(line_number, indent, depth))
            continue

        # Compute depth
        depth = indent // indent_size

        # Strict mode validation
        if strict:
            # Check for tabs in indentation
            if '\t' in raw[:indent]:
                raise TOONDecodeError(
                    f"Line {line_number}: Tabs are not allowed in indentation"
                )

            # Check for exact multiples of indent_size
            if indent > 0 and indent % indent_size != 0:
                raise TOONDecodeError(
                    f"Line {line_number}: Indentation must be exact multiple of "
                    f"{indent_size}, but found {indent} spaces"
                )

        parsed.append(ParsedLine(raw, indent, content, depth, line_number))

    return ScanResult(parsed, blank_lines)
```

### 4.3 Phase 3: Parser Utilities

Create parsing helpers for headers, primitives, and key-value parsing:

```python
# pytoon/decoder/parser_utils.py

from __future__ import annotations
import re
from typing import Any
from pytoon.decoder.types import ArrayHeaderInfo
from pytoon.core.spec import TOONSpec
from pytoon.utils.errors import TOONDecodeError

def parse_array_header(content: str, default_delimiter: str = ',') -> tuple[ArrayHeaderInfo, str | None] | None:
    """Parse array header from line content.

    Args:
        content: Line content (trimmed)
        default_delimiter: Default delimiter to use

    Returns:
        Tuple of (ArrayHeaderInfo, inline_values) or None if not a header
    """
    # Find bracket segment
    bracket_start = content.find('[')
    if bracket_start == -1:
        return None

    bracket_end = content.find(']', bracket_start)
    if bracket_end == -1:
        return None

    # Must have colon after bracket/brace
    colon_idx = content.find(':', bracket_end)
    if colon_idx == -1:
        return None

    # Extract key (before bracket)
    key = content[:bracket_start].strip() if bracket_start > 0 else None

    # Parse bracket content for length and delimiter
    bracket_content = content[bracket_start + 1:bracket_end]
    length, delimiter = parse_bracket_segment(bracket_content, default_delimiter)

    # Check for fields segment {field1,field2}
    fields = None
    brace_start = content.find('{', bracket_end)
    if brace_start != -1 and brace_start < colon_idx:
        brace_end = content.find('}', brace_start)
        if brace_end != -1 and brace_end < colon_idx:
            fields_content = content[brace_start + 1:brace_end]
            fields = parse_delimited_values(fields_content, delimiter)
            fields = [f.strip() for f in fields]

    # Extract inline values after colon
    after_colon = content[colon_idx + 1:].strip()
    inline_values = after_colon if after_colon else None

    return ArrayHeaderInfo(key, length, delimiter, fields), inline_values

def parse_bracket_segment(content: str, default_delimiter: str = ',') -> tuple[int, str]:
    """Parse bracket segment [N] or [N<delimiter>].

    Args:
        content: Content inside brackets
        default_delimiter: Default delimiter

    Returns:
        Tuple of (length, delimiter)
    """
    delimiter = default_delimiter

    # Check for delimiter suffix
    if content.endswith('\t'):
        delimiter = '\t'
        content = content[:-1]
    elif content.endswith('|'):
        delimiter = '|'
        content = content[:-1]

    try:
        length = int(content)
    except ValueError as e:
        raise TOONDecodeError(f"Invalid array length: {content}") from e

    return length, delimiter

def parse_delimited_values(input_str: str, delimiter: str) -> list[str]:
    """Parse delimiter-separated values respecting quotes.

    Args:
        input_str: Delimited string
        delimiter: Active delimiter character

    Returns:
        List of values (may include quotes for later parsing)
    """
    values: list[str] = []
    value_buffer = ''
    in_quotes = False
    i = 0

    while i < len(input_str):
        char = input_str[i]

        # Handle escape sequences in quotes
        if char == '\\' and i + 1 < len(input_str) and in_quotes:
            value_buffer += char + input_str[i + 1]
            i += 2
            continue

        # Toggle quote state
        if char == '"':
            in_quotes = not in_quotes
            value_buffer += char
            i += 1
            continue

        # Split on delimiter when not in quotes
        if char == delimiter and not in_quotes:
            values.append(value_buffer.strip())
            value_buffer = ''
            i += 1
            continue

        value_buffer += char
        i += 1

    # Add last value
    if value_buffer or values:
        values.append(value_buffer.strip())

    return values

def parse_primitive_token(token: str) -> Any:
    """Parse a primitive value token.

    Args:
        token: Token string

    Returns:
        Parsed Python value (None, bool, int, float, or str)
    """
    trimmed = token.strip()

    if not trimmed:
        return ''

    # Quoted string
    if trimmed.startswith('"') and trimmed.endswith('"') and len(trimmed) >= 2:
        return unescape_string(trimmed[1:-1])

    # Boolean/null literals
    if trimmed == TOONSpec.NULL_VALUE:
        return None
    if trimmed in TOONSpec.BOOLEAN_VALUES:
        return TOONSpec.BOOLEAN_VALUES[trimmed]

    # Numeric literals
    if TOONSpec.INTEGER_PATTERN.match(trimmed):
        return int(trimmed)
    if TOONSpec.FLOAT_PATTERN.match(trimmed):
        value = float(trimmed)
        # Normalize -0 to 0
        if value == 0.0:
            return 0.0
        return value

    # Unquoted string
    return trimmed

def unescape_string(content: str) -> str:
    """Unescape a string content (without quotes).

    Args:
        content: String content

    Returns:
        Unescaped string

    Raises:
        TOONDecodeError: For invalid escape sequences
    """
    result = []
    i = 0

    while i < len(content):
        if content[i] == '\\' and i + 1 < len(content):
            next_char = content[i + 1]
            if next_char == '\\':
                result.append('\\')
            elif next_char == '"':
                result.append('"')
            elif next_char == 'n':
                result.append('\n')
            elif next_char == 'r':
                result.append('\r')
            elif next_char == 't':
                result.append('\t')
            else:
                raise TOONDecodeError(f"Invalid escape sequence: \\{next_char}")
            i += 2
        else:
            result.append(content[i])
            i += 1

    return ''.join(result)

def parse_key_token(content: str, start: int = 0) -> tuple[str, int, bool]:
    """Parse a key from content.

    Args:
        content: Line content
        start: Starting position

    Returns:
        Tuple of (key, end_position_after_colon, was_quoted)

    Raises:
        TOONDecodeError: If key is malformed
    """
    if start < len(content) and content[start] == '"':
        # Quoted key
        closing_quote = find_closing_quote(content, start)
        if closing_quote == -1:
            raise TOONDecodeError("Unterminated quoted key")

        key = unescape_string(content[start + 1:closing_quote])
        pos = closing_quote + 1

        # Expect colon
        if pos >= len(content) or content[pos] != ':':
            raise TOONDecodeError("Missing colon after quoted key")

        return key, pos + 1, True
    else:
        # Unquoted key
        pos = start
        while pos < len(content) and content[pos] != ':':
            pos += 1

        if pos >= len(content):
            raise TOONDecodeError("Missing colon after key")

        key = content[start:pos].strip()
        return key, pos + 1, False

def find_closing_quote(content: str, start: int) -> int:
    """Find closing quote position, handling escapes.

    Args:
        content: String to search
        start: Position of opening quote

    Returns:
        Position of closing quote or -1
    """
    i = start + 1  # Skip opening quote
    while i < len(content):
        if content[i] == '\\' and i + 1 < len(content):
            i += 2  # Skip escape sequence
        elif content[i] == '"':
            return i
        else:
            i += 1
    return -1
```

### 4.4 Phase 4: Core Decoder Implementation

Implement the main decoder with proper indentation tracking:

```python
# pytoon/decoder/core.py

from __future__ import annotations
from typing import Any

from pytoon.decoder.types import ParsedLine, ArrayHeaderInfo
from pytoon.decoder.scanner import LineCursor, scan_lines
from pytoon.decoder.parser_utils import (
    parse_array_header,
    parse_delimited_values,
    parse_primitive_token,
    parse_key_token,
)
from pytoon.utils.errors import TOONDecodeError, TOONValidationError

LIST_ITEM_PREFIX = '- '

def decode_toon(source: str, indent_size: int = 2, strict: bool = True) -> Any:
    """Decode TOON source to Python object.

    Args:
        source: TOON source string
        indent_size: Spaces per indentation level
        strict: Enable strict validation

    Returns:
        Decoded Python value
    """
    scan_result = scan_lines(source, indent_size, strict)

    if not scan_result.lines:
        return {}  # Empty document → empty object

    cursor = LineCursor(scan_result.lines, scan_result.blank_lines)
    return decode_value_from_cursor(cursor, indent_size, strict)

def decode_value_from_cursor(cursor: LineCursor, indent_size: int, strict: bool) -> Any:
    """Decode value starting from cursor position.

    Args:
        cursor: Line cursor
        indent_size: Indentation size
        strict: Strict mode

    Returns:
        Decoded Python value
    """
    first = cursor.peek()
    if not first:
        raise TOONDecodeError("No content to decode")

    # Check for root array header
    header_result = parse_array_header(first.content)
    if header_result and not header_result[0].key:
        cursor.advance()
        return decode_array_from_header(header_result[0], header_result[1], cursor, 0, indent_size, strict)

    # Check for single primitive (one line, no colon)
    if len(cursor._lines) == 1 and ':' not in first.content:
        return parse_primitive_token(first.content.strip())

    # Default to object
    return decode_object(cursor, 0, indent_size, strict)

def decode_object(cursor: LineCursor, base_depth: int, indent_size: int, strict: bool) -> dict[str, Any]:
    """Decode an object at given depth.

    Args:
        cursor: Line cursor
        base_depth: Expected depth of object fields
        indent_size: Indentation size
        strict: Strict mode

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
            key, value = decode_key_value(line.content, cursor, computed_depth, indent_size, strict)
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

    Args:
        content: Line content (after indentation)
        cursor: Line cursor for reading nested structures
        base_depth: Current nesting depth
        indent_size: Indentation size
        strict: Strict mode

    Returns:
        Tuple of (key, value)
    """
    # Check for array header (key with [N])
    header_result = parse_array_header(content)
    if header_result and header_result[0].key:
        value = decode_array_from_header(
            header_result[0], header_result[1], cursor, base_depth, indent_size, strict
        )
        return header_result[0].key, value

    # Regular key-value pair
    key, after_colon, _ = parse_key_token(content, 0)
    rest = content[after_colon:].strip()

    if not rest:
        # No value after colon → nested object or empty
        next_line = cursor.peek()
        if next_line and next_line.depth > base_depth:
            nested = decode_object(cursor, base_depth + 1, indent_size, strict)
            return key, nested
        # Empty object
        return key, {}

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

    Args:
        header: Parsed header info
        inline_values: Values after colon (if inline)
        cursor: Line cursor
        base_depth: Array depth
        indent_size: Indentation size
        strict: Strict mode

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

def decode_inline_array(header: ArrayHeaderInfo, values_str: str, strict: bool) -> list[Any]:
    """Decode inline primitive array.

    Args:
        header: Array header info
        values_str: Delimiter-separated values
        strict: Strict mode

    Returns:
        List of primitives
    """
    if not values_str.strip():
        if strict and header.length != 0:
            raise TOONValidationError(
                f"Array declares {header.length} items but found 0"
            )
        return []

    values = parse_delimited_values(values_str, header.delimiter)
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
        strict: Strict mode

    Returns:
        List of dictionaries
    """
    objects: list[dict[str, Any]] = []
    row_depth = base_depth + 1

    while not cursor.at_end() and len(objects) < header.length:
        line = cursor.peek()
        if not line or line.depth < row_depth:
            break

        if line.depth == row_depth:
            cursor.advance()
            values = parse_delimited_values(line.content, header.delimiter)

            if strict and len(values) != len(header.fields or []):
                raise TOONValidationError(
                    f"Row has {len(values)} values but expected {len(header.fields or [])} fields"
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
        strict: Strict mode

    Returns:
        List of values
    """
    items: list[Any] = []
    item_depth = base_depth + 1

    while not cursor.at_end() and len(items) < header.length:
        line = cursor.peek()
        if not line or line.depth < item_depth:
            break

        # Check for list item marker
        is_list_item = (
            line.content.startswith(LIST_ITEM_PREFIX) or
            line.content == '-'
        )

        if line.depth == item_depth and is_list_item:
            item = decode_list_item(cursor, item_depth, indent_size, strict)
            items.append(item)
        else:
            break

    if strict and len(items) != header.length:
        raise TOONValidationError(
            f"Array declares {header.length} items but found {len(items)}"
        )

    return items

def decode_list_item(cursor: LineCursor, base_depth: int, indent_size: int, strict: bool) -> Any:
    """Decode a single list item.

    Args:
        cursor: Line cursor
        base_depth: List item depth
        indent_size: Indentation size
        strict: Strict mode

    Returns:
        Decoded item value
    """
    line = cursor.next()
    if not line:
        raise TOONDecodeError("Expected list item")

    # Extract content after "- "
    if line.content == '-':
        # Empty list item → empty object
        return {}
    elif line.content.startswith(LIST_ITEM_PREFIX):
        after_hyphen = line.content[len(LIST_ITEM_PREFIX):]
    else:
        raise TOONDecodeError(f"Expected list item to start with '{LIST_ITEM_PREFIX}'")

    if not after_hyphen.strip():
        # Empty content after hyphen → empty object
        return {}

    # Check for nested array header (- [N]: ...)
    header_result = parse_array_header(after_hyphen)
    if header_result:
        return decode_array_from_header(
            header_result[0], header_result[1], cursor, base_depth, indent_size, strict
        )

    # Check for object (has colon → first field on hyphen line)
    if ':' in after_hyphen:
        return decode_object_from_list_item(after_hyphen, cursor, base_depth, indent_size, strict)

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

    The first field is on the hyphen line (after "- ").
    Subsequent fields are at base_depth + 1.

    Args:
        first_field_content: Content after "- " on hyphen line
        cursor: Line cursor
        base_depth: List item depth
        indent_size: Indentation size
        strict: Strict mode

    Returns:
        Decoded dictionary

    Notes:
        Per TOON v2.0 §10:
        - First field on hyphen line
        - If first field is nested object, its contents are at depth +2
        - Subsequent sibling fields are at depth +1
    """
    # Parse first field (on hyphen line)
    key, value = decode_key_value(first_field_content, cursor, base_depth, indent_size, strict)
    obj: dict[str, Any] = {key: value}

    # Determine follow depth for sibling fields
    # This is base_depth + 1 (one level deeper than the hyphen line)
    follow_depth = base_depth + 1

    # Read subsequent fields at follow_depth
    while not cursor.at_end():
        line = cursor.peek()
        if not line or line.depth < follow_depth:
            break

        # Check if this is a sibling field at the expected depth
        if line.depth == follow_depth and not line.content.startswith(LIST_ITEM_PREFIX):
            cursor.advance()
            k, v = decode_key_value(line.content, cursor, follow_depth, indent_size, strict)
            obj[k] = v
        else:
            # Different depth or new list item → stop
            break

    return obj
```

### 4.5 Phase 5: Encoder Fixes

Fix the encoder to properly format objects in list items:

```python
# pytoon/encoder/list_encoder.py

def encode_list_item_object(obj: dict[str, Any], depth: int, indent_size: int) -> list[str]:
    """Encode an object as a list item per TOON v2.0 §10.

    Args:
        obj: Dictionary to encode
        depth: List item depth
        indent_size: Spaces per level

    Returns:
        List of lines (first line includes "- ")
    """
    if not obj:
        # Empty object
        return [f"{' ' * (indent_size * depth)}-"]

    lines: list[str] = []
    keys = list(obj.keys())
    base_indent = ' ' * (indent_size * depth)
    field_indent = ' ' * (indent_size * (depth + 1))

    # First field goes on hyphen line
    first_key = keys[0]
    first_value = obj[first_key]

    if isinstance(first_value, dict) and first_value:
        # Nested object: first line is "- key:", nested at depth + 2
        lines.append(f"{base_indent}- {first_key}:")
        nested_indent = ' ' * (indent_size * (depth + 2))
        for nested_key, nested_val in first_value.items():
            encoded = encode_value(nested_val, depth + 2, indent_size)
            if '\n' in encoded:
                lines.append(f"{nested_indent}{nested_key}:")
                for sub_line in encoded.split('\n'):
                    lines.append(f"{nested_indent}{' ' * indent_size}{sub_line}")
            else:
                lines.append(f"{nested_indent}{nested_key}: {encoded}")
    elif isinstance(first_value, list):
        # Array value: header on hyphen line
        encoded = encode_value(first_value, depth + 1, indent_size)
        lines.append(f"{base_indent}- {first_key}{encoded}")
    else:
        # Primitive value on hyphen line
        encoded = encode_value(first_value, depth + 1, indent_size)
        lines.append(f"{base_indent}- {first_key}: {encoded}")

    # Subsequent fields at depth + 1
    for key in keys[1:]:
        value = obj[key]
        encoded = encode_value(value, depth + 1, indent_size)

        if isinstance(value, dict) and value:
            # Nested object
            lines.append(f"{field_indent}{key}:")
            nested_lines = encode_nested_object(value, depth + 2, indent_size)
            lines.extend(nested_lines)
        elif '\n' in encoded:
            # Multi-line value (array)
            lines.append(f"{field_indent}{key}{encoded}")
        else:
            lines.append(f"{field_indent}{key}: {encoded}")

    return lines
```

---

## 5. Testing Strategy

### 5.1 Unit Tests for Scanner

```python
def test_scan_lines_computes_depth():
    source = """
name: Alice
meta:
  created: 2025
  tags:
    - python
    - toon
""".strip()
    result = scan_lines(source, indent_size=2, strict=True)

    assert result.lines[0].depth == 0  # "name: Alice"
    assert result.lines[1].depth == 0  # "meta:"
    assert result.lines[2].depth == 1  # "  created: 2025"
    assert result.lines[3].depth == 1  # "  tags:"
    assert result.lines[4].depth == 2  # "    - python"
    assert result.lines[5].depth == 2  # "    - toon"

def test_strict_mode_rejects_tabs():
    source = "\tname: Alice"
    with pytest.raises(TOONDecodeError, match="Tabs are not allowed"):
        scan_lines(source, indent_size=2, strict=True)

def test_strict_mode_rejects_bad_indent():
    source = "   name: Alice"  # 3 spaces, not multiple of 2
    with pytest.raises(TOONDecodeError, match="exact multiple"):
        scan_lines(source, indent_size=2, strict=True)
```

### 5.2 Integration Tests for Nested Objects in List Arrays

```python
def test_list_array_with_nested_objects_roundtrips():
    """Critical test: nested objects in list-format arrays."""
    data = [
        {'id': 1, 'meta': {'created': '2025', 'active': True}},
        {'id': 2, 'meta': {'created': '2024', 'active': False}},
    ]

    encoder = Encoder()
    encoded = encoder.encode(data)

    # Verify encoding structure
    assert '- id: 1' in encoded
    assert 'meta:' in encoded
    assert 'created: "2025"' in encoded

    decoder = Decoder()
    decoded = decoder.decode(encoded)

    assert decoded == data

def test_object_with_array_in_list_item():
    """Test array as first field in list item."""
    data = [
        {'tags': ['python', 'toon'], 'count': 2},
        {'tags': ['json', 'yaml'], 'count': 2},
    ]

    encoded = encode(data)
    decoded = decode(encoded)

    assert decoded == data

def test_deeply_nested_in_list():
    """Test deeply nested structures in list items."""
    data = [
        {
            'user': {
                'profile': {
                    'name': 'Alice',
                    'settings': {'theme': 'dark'}
                }
            },
            'active': True
        }
    ]

    encoded = encode(data)
    decoded = decode(encoded)

    assert decoded == data
```

### 5.3 Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(st.lists(
    st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        st.recursive(
            st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False)),
            lambda children: st.dictionaries(
                st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L',))),
                children
            )
        )
    ),
    min_size=1,
    max_size=10
))
def test_nested_objects_in_list_roundtrip(data):
    """Property test: any list of nested objects should roundtrip."""
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data
```

---

## 6. Migration Path

### 6.1 Backward Compatibility

The new decoder should be a drop-in replacement:

```python
# pytoon/__init__.py

def decode(
    toon_string: str,
    *,
    strict: bool = True,
    expand_paths: str = "off",
    indent: int = 2,
) -> Any:
    """Decode TOON string to Python object."""
    from pytoon.decoder.core import decode_toon
    return decode_toon(toon_string, indent_size=indent, strict=strict)
```

### 6.2 Deprecation Strategy

1. Keep old decoder as `_decode_legacy()` for comparison
2. Run both decoders in test suite to identify behavioral differences
3. Remove legacy decoder after validation phase

---

## 7. Performance Considerations

### 7.1 Scanner Overhead

Pre-scanning adds one pass over the input, but:

- O(n) time complexity maintained
- Depth computation is O(1) per line
- Enables O(1) depth lookups during parsing

### 7.2 Memory Usage

- ParsedLine objects add memory overhead
- Tradeoff: Higher memory for correctness and maintainability
- Consider lazy line parsing for very large documents

### 7.3 Optimization Opportunities

1. **Lazy scanning**: Only parse lines as needed
2. **Interned strings**: Share common key strings
3. **Streaming**: Process lines without buffering entire document

---

## 8. Success Criteria

1. **Correctness**: All nested object combinations roundtrip correctly
2. **Spec Compliance**: Passes TOON v2.0 conformance test suite
3. **Performance**: <100ms for 1-10KB datasets (unchanged)
4. **Test Coverage**: 85%+ coverage maintained
5. **Type Safety**: mypy strict mode passes
6. **Zero Regressions**: All existing tests pass

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing valid encodings | Extensive roundtrip testing with property-based tests |
| Performance regression | Benchmark before/after; optimize scanner if needed |
| Increased complexity | Clear separation of concerns; comprehensive documentation |
| Spec interpretation errors | Cross-reference with TypeScript implementation |

---

## 10. Timeline Estimate

- **Day 1**: Implement Scanner and LineCursor
- **Day 2**: Implement parser utilities (headers, primitives, escaping)
- **Day 3**: Implement core decoder with depth tracking
- **Day 4**: Fix encoder for proper list-item object formatting
- **Day 5**: Integration testing and edge case handling

---

## 11. References

1. [TOON v2.0 Specification](https://github.com/toon-format/spec/blob/main/SPEC.md)
2. [TypeScript Reference Implementation](https://github.com/toon-format/toon/tree/main/packages/toon/src/decode)
3. [PyToon Current Decoder](pytoon/core/decoder.py)
4. [PyToon Issue Analysis](docs/architecture/DECODER_INDENTATION_REFACTORING.md)

---

## 12. Appendix: Conformance Test Cases

Based on TOON v2.0 §10 and Appendix A, these cases MUST pass:

```toon
# Case 1: Simple object in list
items[2]:
  - id: 1
    name: First
  - id: 2
    name: Second

# Case 2: Nested object as first field
items[1]:
  - meta:
      created: 2025
      version: 1
    status: active

# Case 3: Array as first field
items[1]:
  - users[2]{id,name}:
      1,Ada
      2,Bob
    status: active

# Case 4: Deeply nested
items[1]:
  - config:
      database:
        host: localhost
        port: 5432
    enabled: true
```

Each case validates proper indentation tracking and depth-based parsing.
