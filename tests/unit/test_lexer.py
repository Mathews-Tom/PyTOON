"""Unit tests for Lexer class.

Tests cover:
- Token type recognition
- String handling (quoted/unquoted)
- Number parsing
- Boolean and null keywords
- Array headers
- Indentation tracking
- Error handling with position info
"""

import pytest

from pytoon.decoder.lexer import Lexer, Token, TokenType
from pytoon.utils.errors import TOONDecodeError


class TestTokenType:
    """Test TokenType enum."""

    def test_all_token_types_defined(self) -> None:
        """Test that all expected token types are defined."""
        expected = {
            "IDENTIFIER",
            "STRING",
            "NUMBER",
            "BOOLEAN",
            "NULL",
            "COLON",
            "NEWLINE",
            "INDENT",
            "DEDENT",
            "ARRAY_HEADER",
            "ARRAY_TABULAR_HEADER",
            "DASH",
            "EOF",
        }
        actual = {t.name for t in TokenType}
        assert actual == expected

    def test_token_type_comparison(self) -> None:
        """Test token type comparison."""
        assert TokenType.IDENTIFIER != TokenType.STRING
        assert TokenType.BOOLEAN == TokenType.BOOLEAN


class TestToken:
    """Test Token dataclass."""

    def test_token_creation(self) -> None:
        """Test creating a token."""
        token = Token(TokenType.IDENTIFIER, "name", 1, 1)
        assert token.type == TokenType.IDENTIFIER
        assert token.value == "name"
        assert token.line == 1
        assert token.column == 1

    def test_token_immutable(self) -> None:
        """Test that tokens are immutable (frozen)."""
        token = Token(TokenType.NUMBER, "42", 1, 1)
        with pytest.raises(AttributeError):
            token.value = "100"  # type: ignore[misc]

    def test_token_repr(self) -> None:
        """Test token string representation."""
        token = Token(TokenType.STRING, "hello", 2, 5)
        r = repr(token)
        assert "STRING" in r
        assert "'hello'" in r
        assert "line=2" in r
        assert "col=5" in r


class TestBasicTokenization:
    """Test basic tokenization functionality."""

    def test_empty_input(self) -> None:
        """Test tokenizing empty input."""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        # Empty input just returns EOF (no NEWLINE needed for empty)
        assert len(tokens) >= 1
        assert tokens[-1].type == TokenType.EOF

    def test_single_identifier(self) -> None:
        """Test tokenizing single identifier."""
        lexer = Lexer("name")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "name"

    def test_identifier_with_colon(self) -> None:
        """Test identifier followed by colon."""
        lexer = Lexer("key:")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "key"
        assert tokens[1].type == TokenType.COLON
        assert tokens[1].value == ":"

    def test_simple_key_value(self) -> None:
        """Test simple key-value pair."""
        lexer = Lexer("name: Alice")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-2]]  # Exclude NEWLINE and EOF
        assert types == [TokenType.IDENTIFIER, TokenType.COLON, TokenType.IDENTIFIER]
        assert tokens[2].value == "Alice"

    def test_multiple_lines(self) -> None:
        """Test tokenizing multiple lines."""
        source = "name: Alice\nage: 30"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        newline_count = sum(1 for t in tokens if t.type == TokenType.NEWLINE)
        assert newline_count >= 1


class TestStringTokenization:
    """Test string tokenization."""

    def test_quoted_string(self) -> None:
        """Test quoted string parsing."""
        lexer = Lexer('value: "hello world"')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == "hello world"

    def test_quoted_string_with_escape(self) -> None:
        """Test quoted string with escape sequences."""
        lexer = Lexer('msg: "line1\\nline2"')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == "line1\nline2"

    def test_quoted_string_with_tab_escape(self) -> None:
        """Test tab escape in string."""
        lexer = Lexer('text: "col1\\tcol2"')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == "col1\tcol2"

    def test_quoted_string_with_quote_escape(self) -> None:
        """Test escaped quote in string."""
        lexer = Lexer('text: "say \\"hello\\""')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == 'say "hello"'

    def test_quoted_string_with_backslash_escape(self) -> None:
        """Test escaped backslash in string."""
        lexer = Lexer('path: "C:\\\\Users"')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == "C:\\Users"

    def test_empty_quoted_string(self) -> None:
        """Test empty quoted string."""
        lexer = Lexer('empty: ""')
        tokens = lexer.tokenize()
        string_token = [t for t in tokens if t.type == TokenType.STRING][0]
        assert string_token.value == ""

    def test_unquoted_string(self) -> None:
        """Test unquoted string value (identifier)."""
        lexer = Lexer("status: active")
        tokens = lexer.tokenize()
        # Unquoted strings are parsed as IDENTIFIER
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "active"


class TestNumberTokenization:
    """Test number tokenization."""

    def test_integer(self) -> None:
        """Test integer number."""
        lexer = Lexer("count: 42")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "42"

    def test_negative_integer(self) -> None:
        """Test negative integer."""
        lexer = Lexer("offset: -10")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "-10"

    def test_float(self) -> None:
        """Test floating point number."""
        lexer = Lexer("price: 19.99")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "19.99"

    def test_negative_float(self) -> None:
        """Test negative float."""
        lexer = Lexer("temp: -3.14")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "-3.14"

    def test_zero(self) -> None:
        """Test zero value."""
        lexer = Lexer("zero: 0")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "0"

    def test_large_number(self) -> None:
        """Test large number."""
        lexer = Lexer("big: 1234567890")
        tokens = lexer.tokenize()
        num_token = [t for t in tokens if t.type == TokenType.NUMBER][0]
        assert num_token.value == "1234567890"


class TestBooleanAndNull:
    """Test boolean and null keyword tokenization."""

    def test_true(self) -> None:
        """Test true keyword."""
        lexer = Lexer("enabled: true")
        tokens = lexer.tokenize()
        bool_token = [t for t in tokens if t.type == TokenType.BOOLEAN][0]
        assert bool_token.value == "true"

    def test_false(self) -> None:
        """Test false keyword."""
        lexer = Lexer("disabled: false")
        tokens = lexer.tokenize()
        bool_token = [t for t in tokens if t.type == TokenType.BOOLEAN][0]
        assert bool_token.value == "false"

    def test_null(self) -> None:
        """Test null keyword."""
        lexer = Lexer("optional: null")
        tokens = lexer.tokenize()
        null_token = [t for t in tokens if t.type == TokenType.NULL][0]
        assert null_token.value == "null"


class TestArrayHeaders:
    """Test array header tokenization."""

    def test_simple_array_header(self) -> None:
        """Test simple array header [N]."""
        lexer = Lexer("items: [3]")
        tokens = lexer.tokenize()
        header = [t for t in tokens if t.type == TokenType.ARRAY_HEADER][0]
        assert header.value == "[3]"

    def test_large_array_header(self) -> None:
        """Test array header with large count."""
        lexer = Lexer("data: [100]")
        tokens = lexer.tokenize()
        header = [t for t in tokens if t.type == TokenType.ARRAY_HEADER][0]
        assert header.value == "[100]"

    def test_empty_array_header(self) -> None:
        """Test empty array [0]."""
        lexer = Lexer("empty: [0]")
        tokens = lexer.tokenize()
        header = [t for t in tokens if t.type == TokenType.ARRAY_HEADER][0]
        assert header.value == "[0]"

    def test_tabular_array_header(self) -> None:
        """Test tabular array header with fields."""
        lexer = Lexer("users: [2]{id,name,email}")
        tokens = lexer.tokenize()
        header = [t for t in tokens if t.type == TokenType.ARRAY_TABULAR_HEADER][0]
        assert header.value == "[2]{id,name,email}"

    def test_tabular_header_single_field(self) -> None:
        """Test tabular header with single field."""
        lexer = Lexer("items: [3]{value}")
        tokens = lexer.tokenize()
        header = [t for t in tokens if t.type == TokenType.ARRAY_TABULAR_HEADER][0]
        assert header.value == "[3]{value}"


class TestIndentation:
    """Test indentation handling."""

    def test_simple_indent(self) -> None:
        """Test single level indentation."""
        source = "parent:\n  child: value"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        indent_tokens = [t for t in tokens if t.type == TokenType.INDENT]
        assert len(indent_tokens) == 1

    def test_multiple_indent_levels(self) -> None:
        """Test multiple indentation levels."""
        source = "a:\n  b:\n    c: value"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        indent_tokens = [t for t in tokens if t.type == TokenType.INDENT]
        assert len(indent_tokens) == 2

    def test_dedent(self) -> None:
        """Test dedentation."""
        source = "a:\n  b: 1\nc: 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]
        assert len(dedent_tokens) >= 1

    def test_multiple_dedent(self) -> None:
        """Test multiple dedentation levels."""
        source = "a:\n  b:\n    c: 1\nd: 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]
        assert len(dedent_tokens) >= 2


class TestDashToken:
    """Test dash token for list items."""

    def test_dash_item(self) -> None:
        """Test dash for list item."""
        source = "- item"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        dash_tokens = [t for t in tokens if t.type == TokenType.DASH]
        assert len(dash_tokens) == 1
        assert dash_tokens[0].value == "-"


class TestPositionTracking:
    """Test line and column position tracking."""

    def test_first_token_position(self) -> None:
        """Test position of first token."""
        lexer = Lexer("name: value")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1

    def test_second_line_position(self) -> None:
        """Test position on second line."""
        lexer = Lexer("first: 1\nsecond: 2")
        tokens = lexer.tokenize()
        # Find 'second' identifier
        second_token = [t for t in tokens if t.value == "second"][0]
        assert second_token.line == 2

    def test_column_tracking(self) -> None:
        """Test column position tracking."""
        lexer = Lexer("key: value")
        tokens = lexer.tokenize()
        # 'value' starts at column 6 (after "key: ")
        value_token = [t for t in tokens if t.value == "value"][0]
        assert value_token.column == 6


class TestErrorHandling:
    """Test error handling with position information."""

    def test_unexpected_character_error(self) -> None:
        """Test error on unexpected character."""
        lexer = Lexer("key: @invalid")
        with pytest.raises(TOONDecodeError, match="Unexpected character"):
            lexer.tokenize()

    def test_unterminated_string_error(self) -> None:
        """Test error on unterminated string."""
        lexer = Lexer('key: "unterminated')
        with pytest.raises(TOONDecodeError, match="Unterminated string"):
            lexer.tokenize()

    def test_unterminated_string_newline(self) -> None:
        """Test error when string contains newline."""
        lexer = Lexer('key: "bad\nstring"')
        with pytest.raises(TOONDecodeError, match="Unterminated string"):
            lexer.tokenize()

    def test_invalid_array_header(self) -> None:
        """Test error on invalid array header."""
        lexer = Lexer("items: []")
        with pytest.raises(TOONDecodeError, match="Expected number"):
            lexer.tokenize()

    def test_unclosed_field_list(self) -> None:
        """Test error on unclosed field list."""
        lexer = Lexer("data: [2]{id,name")
        with pytest.raises(TOONDecodeError, match="Unclosed field list"):
            lexer.tokenize()

    def test_invalid_dedent(self) -> None:
        """Test error on invalid indentation level."""
        source = "a:\n  b: 1\n c: 2"  # 1 space indent is invalid
        lexer = Lexer(source)
        with pytest.raises(TOONDecodeError, match="Invalid indentation"):
            lexer.tokenize()


class TestDottedIdentifiers:
    """Test dotted identifiers for key folding."""

    def test_dotted_identifier(self) -> None:
        """Test dotted key identifier."""
        lexer = Lexer("user.name: Alice")
        tokens = lexer.tokenize()
        id_token = tokens[0]
        assert id_token.type == TokenType.IDENTIFIER
        assert id_token.value == "user.name"

    def test_deeply_dotted_identifier(self) -> None:
        """Test deeply dotted key."""
        lexer = Lexer("config.db.host.name: localhost")
        tokens = lexer.tokenize()
        id_token = tokens[0]
        assert id_token.value == "config.db.host.name"


class TestComplexInput:
    """Test complex TOON input."""

    def test_nested_object(self) -> None:
        """Test nested object structure."""
        source = """user:
  name: Alice
  age: 30"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        # Should have IDENTIFIER, COLON, NEWLINE, INDENT, IDENTIFIER, COLON, etc.
        types = [t.type for t in tokens]
        assert TokenType.INDENT in types
        assert types.count(TokenType.IDENTIFIER) >= 3

    def test_array_with_data(self) -> None:
        """Test array header followed by data."""
        source = """items: [2]
- first
- second"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert TokenType.ARRAY_HEADER in [t.type for t in tokens]
        assert TokenType.DASH in [t.type for t in tokens]


class TestLexerProperties:
    """Test Lexer properties and state."""

    def test_source_property(self) -> None:
        """Test source property."""
        source = "test: value"
        lexer = Lexer(source)
        assert lexer.source == source

    def test_initial_position(self) -> None:
        """Test initial position."""
        lexer = Lexer("test")
        assert lexer.pos == 0
        assert lexer.line == 1
        assert lexer.column == 1

    def test_repr(self) -> None:
        """Test lexer repr."""
        lexer = Lexer("test")
        r = repr(lexer)
        assert "Lexer" in r
        assert "pos=" in r
        assert "line=" in r
        assert "col=" in r
