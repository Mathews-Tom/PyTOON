"""Token counting utilities for PyToon.

This module provides token counting functionality for comparing TOON vs JSON
token usage. It uses tiktoken (optional) for accurate GPT-5 o200k_base
token counting with fallback to character-based estimation.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

# Attempt to import tiktoken, set flag if unavailable
_tiktoken_module: Any = None
try:
    import tiktoken as _tiktoken_module  # type: ignore[import-not-found, no-redef]

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


class TokenComparison(TypedDict):
    """Result of comparing JSON vs TOON token counts.

    Attributes:
        json_tokens: Number of tokens in JSON representation.
        toon_tokens: Number of tokens in TOON representation.
        savings_percent: Percentage of token savings (positive = TOON is better).
        json_size: JSON string length in characters.
        toon_size: TOON string length in characters.
    """

    json_tokens: int
    toon_tokens: int
    savings_percent: float
    json_size: int
    toon_size: int


class TokenCounter:
    """Token counter for comparing JSON vs TOON token usage.

    This class provides token counting functionality using tiktoken's o200k_base
    encoding (GPT-5 compatible) when available, or falls back to character-based
    estimation when tiktoken is not installed.

    The character-based fallback uses the approximation: tokens ~= len(text) / 4,
    which provides a reasonable estimate for English text and code.

    Attributes:
        encoding: The tiktoken encoding instance (None if tiktoken unavailable).
        has_tiktoken: Whether tiktoken is available for accurate counting.

    Examples:
        >>> counter = TokenCounter()
        >>> counter.count_tokens("Hello, world!")
        4
        >>> comparison = counter.compare({"name": "Alice", "age": 30})
        >>> comparison["savings_percent"] > 0
        True
        >>> counter.has_tiktoken  # True if tiktoken installed
        True
    """

    def __init__(self) -> None:
        """Initialize TokenCounter with optional tiktoken encoding.

        If tiktoken is installed, uses o200k_base encoding for accurate token
        counting. Otherwise, falls back to character-based estimation.
        """
        self._encoding: Any = None
        self._has_tiktoken = _TIKTOKEN_AVAILABLE

        if self._has_tiktoken and _tiktoken_module is not None:
            try:
                self._encoding = _tiktoken_module.get_encoding("o200k_base")
            except Exception:
                # Fall back to cl100k_base if o200k_base not available
                try:
                    self._encoding = _tiktoken_module.get_encoding("cl100k_base")
                except Exception:
                    # If both fail, disable tiktoken
                    self._has_tiktoken = False
                    self._encoding = None

    @property
    def has_tiktoken(self) -> bool:
        """Check if tiktoken is available for accurate token counting.

        Returns:
            True if tiktoken is installed and working, False otherwise.

        Examples:
            >>> counter = TokenCounter()
            >>> isinstance(counter.has_tiktoken, bool)
            True
        """
        return self._has_tiktoken

    @property
    def encoding(self) -> Any:
        """Get the tiktoken encoding instance.

        Returns:
            The tiktoken Encoding instance, or None if unavailable.
        """
        return self._encoding

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Uses tiktoken's o200k_base encoding when available for accurate counting,
        otherwise falls back to character-based estimation (len(text) // 4).

        Args:
            text: The text string to count tokens for.

        Returns:
            Number of tokens in the text.

        Examples:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello")  # Simple word
            1
            >>> counter.count_tokens("Hello, world!")  # Multiple tokens
            4
            >>> counter.count_tokens("")  # Empty string
            0
            >>> counter.count_tokens("name: Alice\\nage: 30")  # TOON format
            8
        """
        if not text:
            return 0

        if self._has_tiktoken and self._encoding is not None:
            return len(self._encoding.encode(text))

        # Fallback: estimate tokens as characters / 4
        # This is a common approximation for English text and code
        return max(1, len(text) // 4)

    def compare(self, data: Any) -> TokenComparison:
        """Compare token counts between JSON and TOON representations.

        Encodes the provided data to both JSON and TOON formats, counts tokens
        in each, and calculates the percentage savings.

        Args:
            data: Python object to encode and compare (dict, list, or primitive).

        Returns:
            TokenComparison dict with:
                - json_tokens: Token count for JSON representation
                - toon_tokens: Token count for TOON representation
                - savings_percent: Percentage savings (positive = TOON better)
                - json_size: JSON string length
                - toon_size: TOON string length

        Examples:
            >>> counter = TokenCounter()
            >>> result = counter.compare({"name": "Alice", "age": 30})
            >>> "json_tokens" in result
            True
            >>> "toon_tokens" in result
            True
            >>> "savings_percent" in result
            True
            >>> result["savings_percent"] >= 0  # TOON should save tokens
            True
        """
        # Import here to avoid circular imports
        from pytoon import encode

        # Encode to both formats
        json_str = json.dumps(data, separators=(",", ":"))
        toon_str = encode(data)

        # Count tokens
        json_tokens = self.count_tokens(json_str)
        toon_tokens = self.count_tokens(toon_str)

        # Calculate savings percentage
        if json_tokens > 0:
            savings_percent = ((json_tokens - toon_tokens) / json_tokens) * 100
        else:
            savings_percent = 0.0

        return {
            "json_tokens": json_tokens,
            "toon_tokens": toon_tokens,
            "savings_percent": round(savings_percent, 2),
            "json_size": len(json_str),
            "toon_size": len(toon_str),
        }

    def format_comparison(self, data: Any) -> str:
        """Format a comparison result as a human-readable string.

        Args:
            data: Python object to encode and compare.

        Returns:
            Formatted string with token comparison statistics.

        Examples:
            >>> counter = TokenCounter()
            >>> output = counter.format_comparison({"name": "Alice"})
            >>> "TOON:" in output
            True
            >>> "JSON:" in output
            True
            >>> "Savings:" in output
            True
        """
        comparison = self.compare(data)
        return (
            f"TOON: {comparison['toon_tokens']} tokens | "
            f"JSON: {comparison['json_tokens']} tokens | "
            f"Savings: {comparison['savings_percent']:.1f}%"
        )
