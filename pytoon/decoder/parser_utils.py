"""Parser utilities for TOON decoder.

Provides helper functions for parsing headers, primitives, keys,
and handling escape sequences per TOON v2.0 specification.
"""

from __future__ import annotations

from typing import Any

from pytoon.core.spec import TOONSpec
from pytoon.decoder.types import ArrayHeaderInfo
from pytoon.utils.errors import TOONDecodeError


def parse_array_header(
    content: str, default_delimiter: str = ","
) -> tuple[ArrayHeaderInfo, str | None] | None:
    """Parse array header from line content.

    Handles various array header formats:
    - `[3]:` - root array with 3 items
    - `key[3]:` - named array with 3 items
    - `[2]{id,name}:` - tabular array with fields
    - `key[3]: 1,2,3` - inline array with values

    Args:
        content: Line content (trimmed of leading indentation)
        default_delimiter: Default delimiter to use (',' or '\\t' or '|')

    Returns:
        Tuple of (ArrayHeaderInfo, inline_values_string) or None if not a header

    Examples:
        >>> parse_array_header("[3]:")
        (ArrayHeaderInfo(key=None, length=3, delimiter=',', fields=None), None)
        >>> parse_array_header("items[2]: a,b")
        (ArrayHeaderInfo(key='items', length=2, delimiter=',', fields=None), 'a,b')
    """
    # Find bracket segment
    bracket_start = content.find("[")
    if bracket_start == -1:
        return None

    bracket_end = content.find("]", bracket_start)
    if bracket_end == -1:
        return None

    # Find colon (required for array header)
    # Must be after bracket and any optional field list
    colon_idx = -1
    search_start = bracket_end + 1

    # Check for optional fields segment {field1,field2}
    brace_start = content.find("{", bracket_end)
    fields: list[str] | None = None

    if brace_start != -1 and brace_start == bracket_end + 1:
        # Has fields segment immediately after ]
        brace_end = content.find("}", brace_start)
        if brace_end != -1:
            fields_content = content[brace_start + 1 : brace_end]
            # Parse field names (simple split, no quotes in field names)
            delimiter = ","  # Fields are always comma-separated
            fields = [f.strip() for f in fields_content.split(delimiter)]
            search_start = brace_end + 1

    # Find colon after bracket/brace segment
    colon_idx = content.find(":", search_start)
    if colon_idx == -1:
        return None

    # Extract key (before bracket)
    key = content[:bracket_start].strip() if bracket_start > 0 else None
    if key == "":
        key = None

    # Check if key contains a colon - this means it's a key-value pair, not an array header
    # e.g., "results: [0]:" should be parsed as key="results" value="[0]:", not as array with key="results:"
    if key and ":" in key:
        return None

    # Parse bracket content for length and delimiter
    bracket_content = content[bracket_start + 1 : bracket_end]
    length, delimiter = parse_bracket_segment(bracket_content, default_delimiter)

    # Extract inline values after colon
    after_colon = content[colon_idx + 1 :].strip()
    inline_values = after_colon if after_colon else None

    return ArrayHeaderInfo(key, length, delimiter, fields), inline_values


def parse_bracket_segment(
    content: str, default_delimiter: str = ","
) -> tuple[int, str]:
    """Parse bracket segment [N] or [N<delimiter>].

    Args:
        content: Content inside brackets (without brackets)
        default_delimiter: Default delimiter if none specified

    Returns:
        Tuple of (length, delimiter)

    Raises:
        TOONDecodeError: If length is not a valid integer

    Examples:
        >>> parse_bracket_segment("3")
        (3, ',')
        >>> parse_bracket_segment("5\\t")
        (5, '\\t')
        >>> parse_bracket_segment("2|")
        (2, '|')
    """
    delimiter = default_delimiter

    # Check for delimiter suffix
    if content.endswith("\t"):
        delimiter = "\t"
        content = content[:-1]
    elif content.endswith("|"):
        delimiter = "|"
        content = content[:-1]

    try:
        length = int(content.strip())
    except ValueError as e:
        raise TOONDecodeError(f"Invalid array header: {content!r}") from e

    if length < 0:
        raise TOONDecodeError(f"Array length cannot be negative: {length}")

    return length, delimiter


def parse_delimited_values(input_str: str, delimiter: str) -> list[str]:
    """Parse delimiter-separated values respecting quotes.

    Handles quoted strings with escape sequences properly.

    Args:
        input_str: Delimited string
        delimiter: Active delimiter character

    Returns:
        List of values (may include quotes for later parsing)

    Examples:
        >>> parse_delimited_values("a,b,c", ",")
        ['a', 'b', 'c']
        >>> parse_delimited_values('"hello, world",test', ",")
        ['"hello, world"', 'test']
    """
    values: list[str] = []
    value_buffer = ""
    in_quotes = False
    i = 0

    while i < len(input_str):
        char = input_str[i]

        # Handle escape sequences in quotes
        if char == "\\" and i + 1 < len(input_str) and in_quotes:
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
            value_buffer = ""
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

    Handles:
    - null → None
    - true/false → bool
    - integers → int
    - floats → float
    - quoted strings → str (unescaped)
    - unquoted strings → str

    Args:
        token: Token string to parse

    Returns:
        Parsed Python value (None, bool, int, float, or str)

    Examples:
        >>> parse_primitive_token("null")
        None
        >>> parse_primitive_token("true")
        True
        >>> parse_primitive_token("42")
        42
        >>> parse_primitive_token('"hello"')
        'hello'
        >>> parse_primitive_token("world")
        'world'
    """
    trimmed = token.strip()

    if not trimmed:
        return ""

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

    Handles standard escape sequences:
    - \\\\ → \\
    - \\" → "
    - \\n → newline
    - \\r → carriage return
    - \\t → tab

    Args:
        content: String content (without surrounding quotes)

    Returns:
        Unescaped string

    Raises:
        TOONDecodeError: For invalid escape sequences

    Examples:
        >>> unescape_string("hello\\\\nworld")
        'hello\\nworld'
        >>> unescape_string("say \\\\"hi\\\\"")
        'say "hi"'
    """
    result: list[str] = []
    i = 0

    while i < len(content):
        if content[i] == "\\" and i + 1 < len(content):
            next_char = content[i + 1]
            if next_char == "\\":
                result.append("\\")
            elif next_char == '"':
                result.append('"')
            elif next_char == "n":
                result.append("\n")
            elif next_char == "r":
                result.append("\r")
            elif next_char == "t":
                result.append("\t")
            else:
                raise TOONDecodeError(f"Invalid escape sequence: \\{next_char}")
            i += 2
        else:
            result.append(content[i])
            i += 1

    return "".join(result)


def parse_key_token(content: str, start: int = 0) -> tuple[str, int, bool]:
    """Parse a key from content.

    Handles both quoted and unquoted keys.

    Args:
        content: Line content
        start: Starting position in content

    Returns:
        Tuple of (key, end_position_after_colon, was_quoted)

    Raises:
        TOONDecodeError: If key is malformed or missing colon

    Examples:
        >>> parse_key_token("name: Alice")
        ('name', 6, False)
        >>> parse_key_token('"quoted key": value')
        ('quoted key', 14, True)
    """
    # Skip leading whitespace
    pos = start
    while pos < len(content) and content[pos] == " ":
        pos += 1

    if pos >= len(content):
        raise TOONDecodeError("Empty key")

    if content[pos] == '"':
        # Quoted key
        closing_quote = find_closing_quote(content, pos)
        if closing_quote == -1:
            raise TOONDecodeError("Unterminated quoted key")

        key = unescape_string(content[pos + 1 : closing_quote])
        pos = closing_quote + 1

        # Skip whitespace before colon
        while pos < len(content) and content[pos] == " ":
            pos += 1

        # Expect colon
        if pos >= len(content) or content[pos] != ":":
            raise TOONDecodeError(f"Missing colon after quoted key {key!r}")

        return key, pos + 1, True
    else:
        # Unquoted key
        key_start = pos
        while pos < len(content) and content[pos] != ":":
            pos += 1

        if pos >= len(content):
            raise TOONDecodeError("Missing colon after key")

        key = content[key_start:pos].strip()
        if not key:
            raise TOONDecodeError("Empty key name")

        return key, pos + 1, False


def find_closing_quote(content: str, start: int) -> int:
    """Find closing quote position, handling escapes.

    Args:
        content: String to search
        start: Position of opening quote

    Returns:
        Position of closing quote or -1 if not found

    Examples:
        >>> find_closing_quote('"hello"', 0)
        6
        >>> find_closing_quote('"escaped\\\\"quote"', 0)
        16
    """
    i = start + 1  # Skip opening quote
    while i < len(content):
        if content[i] == "\\" and i + 1 < len(content):
            i += 2  # Skip escape sequence
        elif content[i] == '"':
            return i
        else:
            i += 1
    return -1
