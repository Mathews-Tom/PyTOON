"""KeyFoldingEngine for collapsing single-key wrapper chains.

This module provides the KeyFoldingEngine class that transforms nested
single-key dictionaries into flattened structures with dotted paths,
optimizing token usage for deeply nested data.
"""

from __future__ import annotations

from typing import Any

from pytoon.utils.validation import is_safe_identifier


class KeyFoldingEngine:
    """Engine for collapsing single-key wrapper chains into dotted paths.

    The KeyFoldingEngine transforms nested dictionaries with single-key chains
    into flattened structures using dotted path notation. This optimization
    reduces token usage for deeply nested data structures.

    Examples:
        >>> engine = KeyFoldingEngine()
        >>> engine.fold({"a": {"b": {"c": 1}}})
        {'a.b.c': 1}
        >>> engine.fold({"a": {"b": 1, "c": 2}})  # Multi-key, no fold
        {'a': {'b': 1, 'c': 2}}
        >>> engine.fold({"a": [1, 2]})  # Non-dict value, no fold
        {'a': [1, 2]}
        >>> engine.fold({"a.b": {"c": 1}})  # Key with dot, no fold
        {'a.b': {'c': 1}}
    """

    def fold(self, obj: dict[str, Any]) -> dict[str, Any]:
        """Collapse single-key wrapper chains into dotted paths.

        Transforms nested dictionaries where each level has exactly one key
        into flattened key-value pairs with dotted path notation.

        Args:
            obj: Dictionary to fold.

        Returns:
            Dictionary with folded keys where applicable.

        Examples:
            >>> engine = KeyFoldingEngine()
            >>> engine.fold({"a": {"b": {"c": 1}}})
            {'a.b.c': 1}
            >>> engine.fold({"config": {"database": {"host": "localhost"}}})
            {'config.database.host': 'localhost'}
            >>> engine.fold({"a": {"b": 1, "c": 2}})
            {'a': {'b': 1, 'c': 2}}
            >>> engine.fold({})
            {}
        """
        if not obj:
            return {}

        result: dict[str, Any] = {}

        for key, value in obj.items():
            folded_key, folded_value = self._fold_chain(key, value)

            # Recursively process the folded value if it's a dict
            if isinstance(folded_value, dict):
                result[folded_key] = self.fold(folded_value)
            elif isinstance(folded_value, list):
                result[folded_key] = self._fold_list(folded_value)
            else:
                result[folded_key] = folded_value

        return result

    def _fold_chain(self, key: str, value: Any) -> tuple[str, Any]:
        """Fold a single key-value chain into a dotted path.

        Args:
            key: The current key.
            value: The current value.

        Returns:
            Tuple of (folded_key, final_value) where folded_key may be
            a dotted path and final_value is the terminal value.
        """
        # Cannot fold if key itself is not safe
        if not self._is_foldable_key(key):
            return key, value

        # Build the folded path
        path_parts: list[str] = [key]
        current_value = value

        # Keep folding while we have a single-key dict with safe key
        while self._can_fold_path(current_value):
            # We know current_value is a dict with exactly one key
            inner_key = next(iter(current_value))
            if not self._is_foldable_key(inner_key):
                break

            path_parts.append(inner_key)
            current_value = current_value[inner_key]

        folded_key = ".".join(path_parts)
        return folded_key, current_value

    def _fold_list(self, items: list[Any]) -> list[Any]:
        """Recursively fold dictionaries within a list.

        Args:
            items: List of items to process.

        Returns:
            List with folded dictionary items.
        """
        result: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                result.append(self.fold(item))
            elif isinstance(item, list):
                result.append(self._fold_list(item))
            else:
                result.append(item)
        return result

    def _is_foldable_key(self, key: str) -> bool:
        """Check if a key is safe for folding.

        A key is foldable if:
        - It matches the safe identifier pattern (starts with letter, contains
          only letters, digits, underscores)
        - It does NOT contain dots (would cause ambiguity)
        - It does NOT contain special characters

        Args:
            key: Key string to check.

        Returns:
            True if the key can be safely folded, False otherwise.

        Examples:
            >>> engine = KeyFoldingEngine()
            >>> engine._is_foldable_key("name")
            True
            >>> engine._is_foldable_key("user_id")
            True
            >>> engine._is_foldable_key("a.b")  # Contains dot
            False
            >>> engine._is_foldable_key("_private")  # Starts with underscore
            False
            >>> engine._is_foldable_key("key-name")  # Contains dash
            False
        """
        return is_safe_identifier(key)

    def _can_fold_path(self, obj: Any) -> bool:
        """Check if an object is a single-key dict that can be folded.

        Args:
            obj: Object to check.

        Returns:
            True if obj is a dict with exactly one key that is a safe identifier.

        Examples:
            >>> engine = KeyFoldingEngine()
            >>> engine._can_fold_path({"a": 1})
            True
            >>> engine._can_fold_path({"a": {"b": 1}})
            True
            >>> engine._can_fold_path({"a": 1, "b": 2})  # Multi-key
            False
            >>> engine._can_fold_path([1, 2])  # Not a dict
            False
            >>> engine._can_fold_path({})  # Empty dict
            False
            >>> engine._can_fold_path({"a.b": 1})  # Key with dot
            False
        """
        if not isinstance(obj, dict):
            return False

        if len(obj) != 1:
            return False

        # Check if the single key is foldable
        key = next(iter(obj))
        return self._is_foldable_key(key)
