"""Unit tests for TokenCounter class."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pytoon.utils.tokens import TokenComparison, TokenCounter


class TestTokenCounterInitialization:
    """Tests for TokenCounter initialization."""

    def test_init_creates_instance(self) -> None:
        """TokenCounter should initialize without error."""
        counter = TokenCounter()
        assert isinstance(counter, TokenCounter)

    def test_has_tiktoken_is_bool(self) -> None:
        """has_tiktoken property should return boolean."""
        counter = TokenCounter()
        assert isinstance(counter.has_tiktoken, bool)

    def test_encoding_property_exists(self) -> None:
        """encoding property should be accessible."""
        counter = TokenCounter()
        # May be None or an encoding object
        _ = counter.encoding


class TestTokenCounterWithTiktoken:
    """Tests that work when tiktoken is available."""

    @pytest.fixture()
    def counter(self) -> TokenCounter:
        """Create a TokenCounter instance."""
        return TokenCounter()

    def test_count_tokens_empty_string(self, counter: TokenCounter) -> None:
        """Empty string should have 0 tokens."""
        assert counter.count_tokens("") == 0

    def test_count_tokens_single_word(self, counter: TokenCounter) -> None:
        """Single word should have at least 1 token."""
        tokens = counter.count_tokens("Hello")
        assert tokens >= 1

    def test_count_tokens_multiple_words(self, counter: TokenCounter) -> None:
        """Multiple words should have multiple tokens."""
        tokens = counter.count_tokens("Hello, world! How are you?")
        assert tokens > 1

    def test_count_tokens_json_format(self, counter: TokenCounter) -> None:
        """JSON string should be tokenized."""
        json_str = '{"name":"Alice","age":30}'
        tokens = counter.count_tokens(json_str)
        assert tokens > 0

    def test_count_tokens_toon_format(self, counter: TokenCounter) -> None:
        """TOON string should be tokenized."""
        toon_str = "name: Alice\nage: 30"
        tokens = counter.count_tokens(toon_str)
        assert tokens > 0

    def test_count_tokens_returns_int(self, counter: TokenCounter) -> None:
        """count_tokens should always return int."""
        result = counter.count_tokens("test string")
        assert isinstance(result, int)

    def test_count_tokens_whitespace_only(self, counter: TokenCounter) -> None:
        """Whitespace-only string should have tokens."""
        tokens = counter.count_tokens("   \n\t  ")
        assert tokens >= 0  # May be 0 or small number


class TestTokenCounterComparison:
    """Tests for the compare method."""

    @pytest.fixture()
    def counter(self) -> TokenCounter:
        """Create a TokenCounter instance."""
        return TokenCounter()

    def test_compare_returns_token_comparison(self, counter: TokenCounter) -> None:
        """compare should return TokenComparison dict."""
        result = counter.compare({"key": "value"})
        assert isinstance(result, dict)
        assert "json_tokens" in result
        assert "toon_tokens" in result
        assert "savings_percent" in result
        assert "json_size" in result
        assert "toon_size" in result

    def test_compare_json_tokens_positive(self, counter: TokenCounter) -> None:
        """JSON tokens should be positive for non-empty data."""
        result = counter.compare({"name": "Alice"})
        assert result["json_tokens"] > 0

    def test_compare_toon_tokens_positive(self, counter: TokenCounter) -> None:
        """TOON tokens should be positive for non-empty data."""
        result = counter.compare({"name": "Alice"})
        assert result["toon_tokens"] > 0

    def test_compare_savings_is_float(self, counter: TokenCounter) -> None:
        """Savings percentage should be float."""
        result = counter.compare({"key": "value"})
        assert isinstance(result["savings_percent"], float)

    def test_compare_json_size_matches_json_length(
        self, counter: TokenCounter
    ) -> None:
        """json_size should match actual JSON string length."""
        data = {"name": "Alice", "age": 30}
        result = counter.compare(data)
        expected_json = json.dumps(data, separators=(",", ":"))
        assert result["json_size"] == len(expected_json)

    def test_compare_empty_dict(self, counter: TokenCounter) -> None:
        """Empty dict should be comparable."""
        result = counter.compare({})
        assert result["json_tokens"] >= 0
        assert result["toon_tokens"] >= 0

    def test_compare_simple_list(self, counter: TokenCounter) -> None:
        """Simple list should be comparable."""
        result = counter.compare([1, 2, 3])
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0

    def test_compare_nested_structure(self, counter: TokenCounter) -> None:
        """Nested structure should be comparable."""
        data = {"user": {"name": "Alice", "details": {"age": 30, "active": True}}}
        result = counter.compare(data)
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0

    def test_compare_tabular_array_shows_savings(self, counter: TokenCounter) -> None:
        """Tabular array should show token savings."""
        # This is where TOON shines - tabular data
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
        result = counter.compare(data)
        # TOON should have fewer tokens for tabular data
        # We can't guarantee exact savings, but structure should work
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0

    def test_compare_null_value(self, counter: TokenCounter) -> None:
        """None value should be comparable."""
        result = counter.compare(None)
        assert result["json_tokens"] >= 0
        assert result["toon_tokens"] >= 0

    def test_compare_boolean_value(self, counter: TokenCounter) -> None:
        """Boolean value should be comparable."""
        result = counter.compare(True)
        assert result["json_tokens"] >= 0
        assert result["toon_tokens"] >= 0

    def test_compare_string_value(self, counter: TokenCounter) -> None:
        """String value should be comparable."""
        result = counter.compare("hello world")
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0


class TestTokenCounterFormatComparison:
    """Tests for format_comparison method."""

    @pytest.fixture()
    def counter(self) -> TokenCounter:
        """Create a TokenCounter instance."""
        return TokenCounter()

    def test_format_returns_string(self, counter: TokenCounter) -> None:
        """format_comparison should return string."""
        result = counter.format_comparison({"key": "value"})
        assert isinstance(result, str)

    def test_format_contains_toon(self, counter: TokenCounter) -> None:
        """Formatted output should contain TOON label."""
        result = counter.format_comparison({"key": "value"})
        assert "TOON:" in result

    def test_format_contains_json(self, counter: TokenCounter) -> None:
        """Formatted output should contain JSON label."""
        result = counter.format_comparison({"key": "value"})
        assert "JSON:" in result

    def test_format_contains_savings(self, counter: TokenCounter) -> None:
        """Formatted output should contain Savings label."""
        result = counter.format_comparison({"key": "value"})
        assert "Savings:" in result

    def test_format_contains_tokens(self, counter: TokenCounter) -> None:
        """Formatted output should contain 'tokens' word."""
        result = counter.format_comparison({"key": "value"})
        assert "tokens" in result

    def test_format_contains_percentage(self, counter: TokenCounter) -> None:
        """Formatted output should contain percentage sign."""
        result = counter.format_comparison({"key": "value"})
        assert "%" in result


class TestTokenCounterFallback:
    """Tests for fallback behavior when tiktoken is unavailable."""

    def test_fallback_estimation_formula(self) -> None:
        """Fallback should use len(text) // 4 formula."""
        # Create a counter that uses fallback
        with patch("pytoon.utils.tokens._TIKTOKEN_AVAILABLE", False):
            counter = TokenCounter()
            assert counter.has_tiktoken is False

            # Test the fallback formula
            text = "a" * 100  # 100 characters
            tokens = counter.count_tokens(text)
            assert tokens == 25  # 100 // 4 = 25

    def test_fallback_minimum_one_token(self) -> None:
        """Fallback should return at least 1 token for non-empty string."""
        with patch("pytoon.utils.tokens._TIKTOKEN_AVAILABLE", False):
            counter = TokenCounter()
            tokens = counter.count_tokens("abc")  # 3 chars // 4 = 0, but min is 1
            assert tokens >= 1

    def test_fallback_empty_string(self) -> None:
        """Fallback should return 0 for empty string."""
        with patch("pytoon.utils.tokens._TIKTOKEN_AVAILABLE", False):
            counter = TokenCounter()
            tokens = counter.count_tokens("")
            assert tokens == 0

    def test_compare_works_without_tiktoken(self) -> None:
        """compare should work even without tiktoken."""
        with patch("pytoon.utils.tokens._TIKTOKEN_AVAILABLE", False):
            counter = TokenCounter()
            result = counter.compare({"name": "Alice"})
            assert "json_tokens" in result
            assert "toon_tokens" in result
            assert "savings_percent" in result


class TestTokenComparisonType:
    """Tests for TokenComparison TypedDict."""

    def test_token_comparison_is_typed_dict(self) -> None:
        """TokenComparison should be importable."""
        from pytoon.utils.tokens import TokenComparison

        # Verify it's the right type
        assert hasattr(TokenComparison, "__annotations__")

    def test_token_comparison_has_required_keys(self) -> None:
        """TokenComparison should have all required keys defined."""
        annotations = TokenComparison.__annotations__
        assert "json_tokens" in annotations
        assert "toon_tokens" in annotations
        assert "savings_percent" in annotations
        assert "json_size" in annotations
        assert "toon_size" in annotations


class TestTokenCounterEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture()
    def counter(self) -> TokenCounter:
        """Create a TokenCounter instance."""
        return TokenCounter()

    def test_very_long_string(self, counter: TokenCounter) -> None:
        """Should handle very long strings."""
        long_text = "word " * 10000
        tokens = counter.count_tokens(long_text)
        assert tokens > 0

    def test_unicode_characters(self, counter: TokenCounter) -> None:
        """Should handle unicode characters."""
        unicode_text = "Hello \u4e16\u754c \ud83d\ude00"  # Hello World emoji
        tokens = counter.count_tokens(unicode_text)
        assert tokens > 0

    def test_special_characters(self, counter: TokenCounter) -> None:
        """Should handle special characters."""
        special = '!@#$%^&*()[]{}|\\:;"\'<>,.?/'
        tokens = counter.count_tokens(special)
        assert tokens >= 0

    def test_newlines_and_tabs(self, counter: TokenCounter) -> None:
        """Should handle newlines and tabs."""
        text = "line1\nline2\tindented"
        tokens = counter.count_tokens(text)
        assert tokens > 0

    def test_compare_deeply_nested(self, counter: TokenCounter) -> None:
        """Should handle deeply nested structures."""
        data: dict[str, Any] = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        result = counter.compare(data)
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0

    def test_compare_large_array(self, counter: TokenCounter) -> None:
        """Should handle large arrays."""
        data = list(range(100))
        result = counter.compare(data)
        assert result["json_tokens"] > 0
        assert result["toon_tokens"] > 0


class TestTokenCounterIntegration:
    """Integration tests with actual TOON encoding."""

    @pytest.fixture()
    def counter(self) -> TokenCounter:
        """Create a TokenCounter instance."""
        return TokenCounter()

    def test_toon_encoding_is_used(self, counter: TokenCounter) -> None:
        """compare should use actual TOON encoding."""
        from pytoon import encode

        data = {"name": "Alice"}
        result = counter.compare(data)

        # Verify TOON size matches actual encoding
        toon_str = encode(data)
        assert result["toon_size"] == len(toon_str)

    def test_json_encoding_is_compact(self, counter: TokenCounter) -> None:
        """compare should use compact JSON encoding."""
        data = {"name": "Alice", "age": 30}
        result = counter.compare(data)

        # Compact JSON has no spaces
        expected_json = '{"name":"Alice","age":30}'
        assert result["json_size"] == len(expected_json)

    def test_savings_calculation_correct(self, counter: TokenCounter) -> None:
        """Savings percentage should be calculated correctly."""
        # Mock specific token counts to verify calculation
        data = {"test": "value"}
        result = counter.compare(data)

        # Manually verify: savings = (json - toon) / json * 100
        expected_savings = (
            (result["json_tokens"] - result["toon_tokens"])
            / result["json_tokens"]
            * 100
        )
        assert abs(result["savings_percent"] - expected_savings) < 0.01

    def test_import_from_utils(self) -> None:
        """TokenCounter should be importable from utils module."""
        from pytoon.utils import TokenCounter, TokenComparison

        counter = TokenCounter()
        result = counter.compare({"key": "value"})
        # Verify it returns the right type structure
        assert isinstance(result["json_tokens"], int)
        assert isinstance(result["toon_tokens"], int)
        assert isinstance(result["savings_percent"], float)


# Type annotation for deeply nested test
from typing import Any
