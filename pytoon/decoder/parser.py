"""Parser for TOON format.

This module provides the Parser class that builds hierarchical Python objects
from a token stream using state machine-based parsing.
"""

from __future__ import annotations

from typing import Any

from pytoon.decoder.lexer import Lexer, Token, TokenType
from pytoon.decoder.pathexpander import PathExpander
from pytoon.decoder.statemachine import ParserState, StateMachine
from pytoon.utils.errors import TOONDecodeError


class Parser:
    """Parses TOON token stream into Python objects.

    The Parser takes a token stream from the Lexer and builds hierarchical
    Python objects (dicts, lists, primitives) using state machine-based
    parsing. It handles nested structures, arrays, and value type conversion.

    Args:
        lexer: Lexer instance with tokenized input
        expand_paths: Whether to expand dotted keys (default: True)

    Examples:
        >>> lexer = Lexer("name: Alice\\nage: 30")
        >>> parser = Parser(lexer)
        >>> result = parser.parse()
        >>> result
        {'name': 'Alice', 'age': 30}

        >>> lexer = Lexer("items: [2]\\n- first\\n- second")
        >>> parser = Parser(lexer)
        >>> result = parser.parse()
        >>> result
        {'items': ['first', 'second']}

    Raises:
        TOONDecodeError: On parsing errors
    """

    def __init__(self, lexer: Lexer, *, expand_paths: bool = True) -> None:
        """Initialize the parser.

        Args:
            lexer: Lexer with tokenized input
            expand_paths: Whether to expand dotted keys to nested dicts
        """
        self._lexer = lexer
        self._tokens: list[Token] = []
        self._pos = 0
        self._state_machine = StateMachine()
        self._path_expander = PathExpander()
        self._expand_paths = expand_paths

    def parse(self) -> Any:
        """Parse the token stream into a Python object.

        Returns:
            Parsed Python object (dict, list, or primitive)

        Raises:
            TOONDecodeError: On parsing errors

        Examples:
            >>> lexer = Lexer("key: value")
            >>> parser = Parser(lexer)
            >>> parser.parse()
            {'key': 'value'}
        """
        self._tokens = self._lexer.tokenize()
        self._pos = 0
        self._state_machine.reset()

        # Skip leading newlines
        self._skip_newlines()

        if self._at_end() or self._peek().type == TokenType.EOF:
            # Empty input
            self._state_machine.transition_to(ParserState.COMPLETE)
            return {}

        # Parse the root structure
        result = self._parse_root()

        # Expand dotted keys if requested
        if self._expand_paths and isinstance(result, dict):
            result = self._path_expander.expand_recursive(result)

        self._state_machine.transition_to(ParserState.COMPLETE)
        return result

    def _parse_root(self) -> Any:
        """Parse the root structure (object or array)."""
        if self._peek().type == TokenType.ARRAY_HEADER:
            return self._parse_list_array()
        elif self._peek().type == TokenType.ARRAY_TABULAR_HEADER:
            return self._parse_tabular_array()
        elif self._peek().type == TokenType.DASH:
            return self._parse_list_array()
        else:
            return self._parse_object()

    def _parse_object(self) -> dict[str, Any]:
        """Parse an object (key-value pairs)."""
        result: dict[str, Any] = {}

        # Only transition if not already in EXPECT_KEY
        if self._state_machine.state != ParserState.EXPECT_KEY:
            self._state_machine.transition_to(ParserState.EXPECT_KEY)

        while not self._at_end():
            self._skip_newlines()

            if self._at_end() or self._peek().type == TokenType.EOF:
                break

            token = self._peek()

            # Handle dedent (end of nested object)
            if token.type == TokenType.DEDENT:
                self._advance()
                break

            # Expect identifier (key)
            if token.type != TokenType.IDENTIFIER:
                break

            key = token.value
            self._advance()

            # Expect colon
            if self._at_end() or self._peek().type != TokenType.COLON:
                raise TOONDecodeError(
                    f"Expected ':' after key {key!r} at line {token.line}"
                )
            self._state_machine.transition_to(ParserState.EXPECT_COLON)
            self._advance()

            # Parse value
            self._state_machine.transition_to(ParserState.EXPECT_VALUE)
            value = self._parse_value()

            if key in result:
                raise TOONDecodeError(f"Duplicate key: {key!r} at line {token.line}")
            result[key] = value

            # Transition back to expecting next key
            if self._state_machine.state == ParserState.EXPECT_VALUE:
                self._state_machine.transition_to(ParserState.EXPECT_KEY)

        return result

    def _parse_value(self) -> Any:
        """Parse a value (primitive, nested object, or array)."""
        self._skip_newlines()

        if self._at_end():
            raise TOONDecodeError("Unexpected end of input while parsing value")

        token = self._peek()

        # Check for nested object (INDENT)
        if token.type == TokenType.INDENT:
            self._advance()
            return self._parse_nested_object()

        # Check for array header
        if token.type == TokenType.ARRAY_HEADER:
            return self._parse_list_array()

        if token.type == TokenType.ARRAY_TABULAR_HEADER:
            return self._parse_tabular_array()

        # Parse inline value
        if token.type == TokenType.STRING:
            self._advance()
            return token.value
        elif token.type == TokenType.NUMBER:
            self._advance()
            return self._convert_number(token.value)
        elif token.type == TokenType.BOOLEAN:
            self._advance()
            return token.value == "true"
        elif token.type == TokenType.NULL:
            self._advance()
            return None
        elif token.type == TokenType.IDENTIFIER:
            # Unquoted string value
            self._advance()
            return token.value
        else:
            raise TOONDecodeError(
                f"Unexpected token {token.type.name} at line {token.line}, "
                f"column {token.column}"
            )

    def _parse_nested_object(self) -> dict[str, Any]:
        """Parse a nested object after INDENT."""
        self._state_machine.transition_to(ParserState.IN_NESTED_OBJECT)
        result = self._parse_object()
        return result

    def _parse_list_array(self) -> list[Any]:
        """Parse a list-style array."""
        items: list[Any] = []

        # Check for array header
        if self._peek().type == TokenType.ARRAY_HEADER:
            header = self._peek()
            count = self._extract_array_count(header.value)
            self._advance()
            self._skip_newlines()

        # Parse list items
        while not self._at_end():
            self._skip_newlines()

            if self._at_end() or self._peek().type == TokenType.EOF:
                break

            if self._peek().type == TokenType.DEDENT:
                self._advance()
                break

            if self._peek().type != TokenType.DASH:
                break

            self._advance()  # consume dash

            # Skip space after dash
            if not self._at_end() and self._peek().type != TokenType.NEWLINE:
                # Parse the item value
                value = self._parse_list_item_value()
                items.append(value)
            else:
                # Empty item or newline
                items.append(None)

        return items

    def _parse_list_item_value(self) -> Any:
        """Parse a single list item value."""
        if self._at_end():
            return None

        token = self._peek()

        if token.type == TokenType.INDENT:
            # Nested object in list
            self._advance()
            return self._parse_nested_object()
        elif token.type == TokenType.STRING:
            self._advance()
            return token.value
        elif token.type == TokenType.NUMBER:
            self._advance()
            return self._convert_number(token.value)
        elif token.type == TokenType.BOOLEAN:
            self._advance()
            return token.value == "true"
        elif token.type == TokenType.NULL:
            self._advance()
            return None
        elif token.type == TokenType.IDENTIFIER:
            self._advance()
            return token.value
        else:
            return None

    def _parse_tabular_array(self) -> list[dict[str, Any]]:
        """Parse a tabular array with field headers."""
        header = self._peek()
        count, fields = self._extract_tabular_info(header.value)
        self._advance()

        rows: list[dict[str, Any]] = []

        # Parse each row
        for _ in range(count):
            self._skip_newlines()
            if self._at_end() or self._peek().type == TokenType.EOF:
                break

            row = self._parse_tabular_row(fields)
            rows.append(row)

        return rows

    def _parse_tabular_row(self, fields: list[str]) -> dict[str, Any]:
        """Parse a single tabular row."""
        row: dict[str, Any] = {}

        for i, field in enumerate(fields):
            if self._at_end() or self._peek().type in (
                TokenType.NEWLINE,
                TokenType.EOF,
            ):
                break

            token = self._peek()

            if token.type == TokenType.STRING:
                self._advance()
                row[field] = token.value
            elif token.type == TokenType.NUMBER:
                self._advance()
                row[field] = self._convert_number(token.value)
            elif token.type == TokenType.BOOLEAN:
                self._advance()
                row[field] = token.value == "true"
            elif token.type == TokenType.NULL:
                self._advance()
                row[field] = None
            elif token.type == TokenType.IDENTIFIER:
                self._advance()
                row[field] = token.value
            else:
                break

        return row

    def _extract_array_count(self, header: str) -> int:
        """Extract count from array header [N]."""
        # header format: "[N]"
        start = header.index("[") + 1
        end = header.index("]")
        return int(header[start:end])

    def _extract_tabular_info(self, header: str) -> tuple[int, list[str]]:
        """Extract count and fields from tabular header [N]{fields}."""
        # header format: "[N]{field1,field2,...}"
        bracket_end = header.index("]")
        count = int(header[1:bracket_end])

        # Extract fields
        brace_start = header.index("{") + 1
        brace_end = header.index("}")
        fields_str = header[brace_start:brace_end]
        fields = [f.strip() for f in fields_str.split(",")]

        return count, fields

    def _convert_number(self, value: str) -> int | float:
        """Convert string to number (int or float)."""
        if "." in value:
            return float(value)
        else:
            return int(value)

    def _peek(self) -> Token:
        """Peek at current token without consuming."""
        if self._pos >= len(self._tokens):
            # Return EOF token
            return Token(TokenType.EOF, "", 0, 0)
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        """Advance to next token and return current."""
        token = self._peek()
        self._pos += 1
        return token

    def _at_end(self) -> bool:
        """Check if at end of token stream."""
        return self._pos >= len(self._tokens)

    def _skip_newlines(self) -> None:
        """Skip NEWLINE tokens."""
        while not self._at_end() and self._peek().type == TokenType.NEWLINE:
            self._advance()

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Parser(pos={self._pos}, "
            f"state={self._state_machine.state.name}, "
            f"expand_paths={self._expand_paths})"
        )
