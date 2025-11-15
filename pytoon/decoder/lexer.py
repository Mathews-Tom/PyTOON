"""Lexer for TOON format tokenization.

This module provides the Lexer class that tokenizes TOON input into a stream
of tokens with position tracking for error reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from pytoon.utils.errors import TOONDecodeError


class TokenType(Enum):
    """Token type enumeration for TOON lexer.

    Token Types:
        IDENTIFIER: Key names (e.g., "name", "config")
        STRING: Quoted or unquoted string values
        NUMBER: Integer or float values
        BOOLEAN: true or false
        NULL: null value
        COLON: ':' separator
        NEWLINE: Line terminator
        INDENT: Indentation increase
        DEDENT: Indentation decrease
        ARRAY_HEADER: Array length marker [N]
        ARRAY_TABULAR_HEADER: Tabular array header [N]{fields}
        DASH: '-' for list items
        EOF: End of file marker

    Examples:
        >>> TokenType.IDENTIFIER.name
        'IDENTIFIER'
        >>> TokenType.ARRAY_HEADER == TokenType.STRING
        False
    """

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    NULL = auto()
    COLON = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    ARRAY_HEADER = auto()
    ARRAY_TABULAR_HEADER = auto()
    DASH = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """Represents a single token from TOON input.

    Attributes:
        type: The token type
        value: The string value of the token
        line: Line number (1-indexed)
        column: Column number (1-indexed)

    Examples:
        >>> token = Token(TokenType.IDENTIFIER, "name", 1, 1)
        >>> token.type
        <TokenType.IDENTIFIER: 1>
        >>> token.value
        'name'
        >>> token.line
        1
    """

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Token({self.type.name}, {self.value!r}, "
            f"line={self.line}, col={self.column})"
        )


class Lexer:
    """Tokenizes TOON input into stream of tokens.

    The Lexer converts TOON formatted text into a sequence of tokens that
    can be processed by the parser. It tracks position (line, column) for
    error reporting and handles indentation-based structure detection.

    Args:
        source: The TOON source text to tokenize

    Attributes:
        source: The input text
        pos: Current position in source
        line: Current line number (1-indexed)
        column: Current column number (1-indexed)

    Examples:
        >>> lexer = Lexer("name: Alice")
        >>> tokens = lexer.tokenize()
        >>> tokens[0].type
        <TokenType.IDENTIFIER: 1>
        >>> tokens[0].value
        'name'

        >>> lexer = Lexer("count: 42")
        >>> tokens = lexer.tokenize()
        >>> tokens[2].type
        <TokenType.NUMBER: 3>

    Raises:
        TOONDecodeError: On invalid input or unexpected characters
    """

    def __init__(self, source: str) -> None:
        """Initialize the lexer with source text.

        Args:
            source: TOON source text to tokenize
        """
        self._source = source
        self._pos = 0
        self._line = 1
        self._column = 1
        self._tokens: list[Token] = []
        self._indent_stack: list[int] = [0]

    @property
    def source(self) -> str:
        """Get the source text."""
        return self._source

    @property
    def pos(self) -> int:
        """Get current position in source."""
        return self._pos

    @property
    def line(self) -> int:
        """Get current line number."""
        return self._line

    @property
    def column(self) -> int:
        """Get current column number."""
        return self._column

    def tokenize(self) -> list[Token]:
        """Tokenize the entire source into a list of tokens.

        Returns:
            List of tokens, always ending with EOF token

        Raises:
            TOONDecodeError: On invalid input

        Examples:
            >>> lexer = Lexer("enabled: true")
            >>> tokens = lexer.tokenize()
            >>> [t.type.name for t in tokens]
            ['IDENTIFIER', 'COLON', 'BOOLEAN', 'NEWLINE', 'EOF']
        """
        self._tokens = []
        self._pos = 0
        self._line = 1
        self._column = 1
        self._indent_stack = [0]

        while not self._at_end():
            self._scan_token()

        # Close any remaining indentation levels
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            self._add_token(TokenType.DEDENT, "")

        # Ensure we have a final NEWLINE if not present
        if self._tokens and self._tokens[-1].type != TokenType.NEWLINE:
            self._add_token(TokenType.NEWLINE, "\\n")

        # Add EOF
        self._add_token(TokenType.EOF, "")

        return self._tokens

    def _scan_token(self) -> None:
        """Scan the next token from source."""
        # Handle start of line indentation
        if self._column == 1:
            self._handle_indentation()
            if self._at_end():
                return

        # Skip spaces (but not at start of line)
        while not self._at_end() and self._peek() == " " and self._column > 1:
            self._advance()

        if self._at_end():
            return

        char = self._peek()

        if char == "\n":
            self._add_token(TokenType.NEWLINE, "\\n")
            self._advance()
            self._line += 1
            self._column = 1
        elif char == ":":
            self._add_token(TokenType.COLON, ":")
            self._advance()
        elif char == "-" and self._peek_next() == " ":
            self._add_token(TokenType.DASH, "-")
            self._advance()
        elif char == "[":
            self._scan_array_header()
        elif char == '"':
            self._scan_quoted_string()
        elif char.isdigit() or (char == "-" and self._is_number_start()):
            self._scan_number()
        elif char.isalpha() or char == "_":
            self._scan_identifier_or_keyword()
        else:
            raise TOONDecodeError(
                f"Unexpected character {char!r} at line {self._line}, column {self._column}"
            )

    def _handle_indentation(self) -> None:
        """Handle indentation at start of line."""
        indent_count = 0
        start_pos = self._pos

        while not self._at_end() and self._peek() == " ":
            indent_count += 1
            self._advance()

        # Skip blank lines
        if not self._at_end() and self._peek() == "\n":
            return

        # Skip comment lines (if we add comments later)
        if self._at_end():
            return

        # Check for dedent
        current_indent = self._indent_stack[-1]

        if indent_count > current_indent:
            # Indent
            self._indent_stack.append(indent_count)
            self._add_token(TokenType.INDENT, " " * indent_count)
        elif indent_count < current_indent:
            # Dedent - may need multiple
            while (
                len(self._indent_stack) > 1 and indent_count < self._indent_stack[-1]
            ):
                if indent_count not in self._indent_stack:
                    raise TOONDecodeError(
                        f"Invalid indentation at line {self._line}: "
                        f"expected one of {self._indent_stack}, got {indent_count}"
                    )
                self._indent_stack.pop()
                self._add_token(TokenType.DEDENT, "")

    def _scan_array_header(self) -> None:
        """Scan array header token [N] or [N]{fields}."""
        start_col = self._column
        self._advance()  # consume '['

        # Read the number
        num_start = self._pos
        while not self._at_end() and self._peek().isdigit():
            self._advance()

        if self._at_end() or self._peek() not in ("]\t", "]"):
            if not self._at_end() and self._peek() != "]":
                raise TOONDecodeError(
                    f"Expected ']' in array header at line {self._line}, column {self._column}"
                )

        num_str = self._source[num_start : self._pos]
        if not num_str:
            raise TOONDecodeError(
                f"Expected number in array header at line {self._line}, column {self._column}"
            )

        # Check for tabular format
        if not self._at_end() and self._peek() == "\t":
            # Tabular format with tab separator
            self._advance()  # consume tab
            if self._at_end() or self._peek() != "]":
                raise TOONDecodeError(
                    f"Expected ']' after tab in array header at line {self._line}"
                )

        if self._at_end():
            raise TOONDecodeError(f"Unexpected end of input in array header")

        self._advance()  # consume ']'

        # Check for field list
        if not self._at_end() and self._peek() == "{":
            self._advance()  # consume '{'
            fields_start = self._pos

            while not self._at_end() and self._peek() != "}":
                self._advance()

            if self._at_end():
                raise TOONDecodeError(
                    f"Unclosed field list in array header at line {self._line}"
                )

            fields = self._source[fields_start : self._pos]
            self._advance()  # consume '}'

            header_value = f"[{num_str}]{{{fields}}}"
            self._add_token_at(
                TokenType.ARRAY_TABULAR_HEADER, header_value, self._line, start_col
            )
        else:
            self._add_token_at(
                TokenType.ARRAY_HEADER, f"[{num_str}]", self._line, start_col
            )

    def _scan_quoted_string(self) -> None:
        """Scan a quoted string."""
        start_col = self._column
        self._advance()  # consume opening quote

        value_chars: list[str] = []
        while not self._at_end() and self._peek() != '"':
            char = self._peek()
            if char == "\n":
                raise TOONDecodeError(
                    f"Unterminated string at line {self._line}, column {start_col}"
                )
            if char == "\\":
                self._advance()
                if self._at_end():
                    raise TOONDecodeError(f"Unexpected end of input in string escape")
                escape_char = self._peek()
                if escape_char == "n":
                    value_chars.append("\n")
                elif escape_char == "t":
                    value_chars.append("\t")
                elif escape_char == "\\":
                    value_chars.append("\\")
                elif escape_char == '"':
                    value_chars.append('"')
                else:
                    value_chars.append(escape_char)
            else:
                value_chars.append(char)
            self._advance()

        if self._at_end():
            raise TOONDecodeError(
                f"Unterminated string at line {self._line}, column {start_col}"
            )

        self._advance()  # consume closing quote
        self._add_token_at(TokenType.STRING, "".join(value_chars), self._line, start_col)

    def _scan_number(self) -> None:
        """Scan a number (integer or float)."""
        start_col = self._column
        start_pos = self._pos
        has_dot = False

        if self._peek() == "-":
            self._advance()

        while not self._at_end():
            char = self._peek()
            if char.isdigit():
                self._advance()
            elif char == "." and not has_dot:
                has_dot = True
                self._advance()
            else:
                break

        value = self._source[start_pos : self._pos]
        self._add_token_at(TokenType.NUMBER, value, self._line, start_col)

    def _scan_identifier_or_keyword(self) -> None:
        """Scan identifier or keyword (true/false/null)."""
        start_col = self._column
        start_pos = self._pos

        while not self._at_end():
            char = self._peek()
            if char.isalnum() or char in ("_", "."):
                self._advance()
            else:
                break

        value = self._source[start_pos : self._pos]

        # Check for keywords
        if value == "true" or value == "false":
            self._add_token_at(TokenType.BOOLEAN, value, self._line, start_col)
        elif value == "null":
            self._add_token_at(TokenType.NULL, value, self._line, start_col)
        else:
            self._add_token_at(TokenType.IDENTIFIER, value, self._line, start_col)

    def _is_number_start(self) -> bool:
        """Check if current position starts a number (after -)."""
        next_char = self._peek_next()
        return next_char is not None and next_char.isdigit()

    def _peek(self) -> str:
        """Peek at current character without consuming."""
        if self._at_end():
            return ""
        return self._source[self._pos]

    def _peek_next(self) -> str | None:
        """Peek at next character without consuming."""
        if self._pos + 1 >= len(self._source):
            return None
        return self._source[self._pos + 1]

    def _advance(self) -> str:
        """Advance position and return consumed character."""
        if self._at_end():
            return ""
        char = self._source[self._pos]
        self._pos += 1
        self._column += 1
        return char

    def _at_end(self) -> bool:
        """Check if at end of source."""
        return self._pos >= len(self._source)

    def _add_token(self, token_type: TokenType, value: str) -> None:
        """Add a token at current position."""
        self._tokens.append(Token(token_type, value, self._line, self._column))

    def _add_token_at(
        self, token_type: TokenType, value: str, line: int, column: int
    ) -> None:
        """Add a token at specific position."""
        self._tokens.append(Token(token_type, value, line, column))

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Lexer(pos={self._pos}, line={self._line}, col={self._column})"
