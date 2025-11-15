"""Path expander for reversing key folding.

This module provides the PathExpander class that reconstructs dotted keys
into nested dictionaries, reversing the key folding operation.
"""

from __future__ import annotations

from typing import Any

from pytoon.utils.errors import TOONDecodeError


class PathExpander:
    """Reverses key folding by expanding dotted keys into nested dicts.

    The PathExpander is responsible for taking flat dictionaries with dotted
    keys (e.g., {"a.b.c": 1}) and reconstructing them into nested structures
    (e.g., {"a": {"b": {"c": 1}}}).

    This operation reverses the key folding performed during encoding.

    Examples:
        >>> expander = PathExpander()
        >>> expander.expand({"a.b.c": 1})
        {'a': {'b': {'c': 1}}}
        >>> expander.expand({"user.name": "Alice", "user.age": 30})
        {'user': {'name': 'Alice', 'age': 30}}
        >>> expander.expand({"simple": "value"})
        {'simple': 'value'}

    Raises:
        TOONDecodeError: On key conflicts during expansion
    """

    def expand(self, data: dict[str, Any]) -> dict[str, Any]:
        """Expand dotted keys into nested dictionaries.

        Takes a dictionary with potentially dotted keys and expands them
        into a nested structure.

        Args:
            data: Dictionary with dotted keys to expand

        Returns:
            Dictionary with nested structure

        Raises:
            TOONDecodeError: If key expansion causes conflicts

        Examples:
            >>> expander = PathExpander()
            >>> expander.expand({"a.b.c": 1})
            {'a': {'b': {'c': 1}}}
            >>> expander.expand({"x": 1, "y.z": 2})
            {'x': 1, 'y': {'z': 2}}
        """
        result: dict[str, Any] = {}

        for key, value in data.items():
            self._set_nested(result, key, value)

        return result

    def _set_nested(self, target: dict[str, Any], key: str, value: Any) -> None:
        """Set a value in a nested dictionary using dotted key path.

        Args:
            target: Target dictionary to modify
            key: Dotted key path (e.g., "a.b.c")
            value: Value to set

        Raises:
            TOONDecodeError: If path conflicts with existing structure
        """
        if "." not in key:
            # Simple key, no expansion needed
            if key in target:
                raise TOONDecodeError(f"Duplicate key: {key!r}")
            target[key] = value
            return

        # Split dotted path
        parts = key.split(".")

        # Traverse/create path
        current = target
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                # Create new nested dict
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Conflict: trying to nest into non-dict
                existing_path = ".".join(parts[: i + 1])
                raise TOONDecodeError(
                    f"Key conflict: {existing_path!r} is not a dictionary, "
                    f"cannot expand {key!r}"
                )

            current = current[part]

        # Set final value
        final_key = parts[-1]
        if final_key in current:
            # Check if it's a conflict
            if isinstance(current[final_key], dict) and not isinstance(value, dict):
                raise TOONDecodeError(
                    f"Key conflict: {key!r} would overwrite nested structure"
                )
            raise TOONDecodeError(f"Duplicate key: {key!r}")

        current[final_key] = value

    def expand_recursive(self, data: Any) -> Any:
        """Recursively expand dotted keys in nested structures.

        Applies expansion to all dictionaries in the structure, including
        those nested within arrays.

        Args:
            data: Any Python structure (dict, list, or primitive)

        Returns:
            Structure with all dotted keys expanded

        Examples:
            >>> expander = PathExpander()
            >>> expander.expand_recursive({"outer.inner": {"nested.key": 1}})
            {'outer': {'inner': {'nested': {'key': 1}}}}
            >>> expander.expand_recursive([{"a.b": 1}, {"c.d": 2}])
            [{'a': {'b': 1}}, {'c': {'d': 2}}]
        """
        if isinstance(data, dict):
            # First expand the values recursively
            expanded_values = {k: self.expand_recursive(v) for k, v in data.items()}
            # Then expand the keys
            return self.expand(expanded_values)
        elif isinstance(data, list):
            return [self.expand_recursive(item) for item in data]
        else:
            return data

    def has_dotted_keys(self, data: dict[str, Any]) -> bool:
        """Check if dictionary contains any dotted keys.

        Args:
            data: Dictionary to check

        Returns:
            True if any key contains '.', False otherwise

        Examples:
            >>> expander = PathExpander()
            >>> expander.has_dotted_keys({"a.b": 1})
            True
            >>> expander.has_dotted_keys({"simple": 1})
            False
        """
        return any("." in key for key in data)

    def validate_no_conflicts(self, data: dict[str, Any]) -> None:
        """Validate that expanding keys won't cause conflicts.

        Pre-validates the dictionary to ensure expansion is safe.

        Args:
            data: Dictionary to validate

        Raises:
            TOONDecodeError: If expansion would cause conflicts

        Examples:
            >>> expander = PathExpander()
            >>> expander.validate_no_conflicts({"a": 1, "a.b": 2})  # Conflict!
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONDecodeError: Key conflict: ...
        """
        # Build path tree to check for conflicts
        path_tree: dict[str, Any] = {}

        for key in data:
            parts = key.split(".")

            current = path_tree
            for i, part in enumerate(parts):
                if part not in current:
                    if i == len(parts) - 1:
                        # This is the final key
                        current[part] = "LEAF"
                    else:
                        # This is an intermediate path
                        current[part] = {}
                else:
                    if i == len(parts) - 1:
                        # Final key conflicts with existing
                        if current[part] == "LEAF":
                            raise TOONDecodeError(f"Duplicate key path: {key!r}")
                        else:
                            # Trying to make intermediate node a leaf
                            existing_path = ".".join(parts[: i + 1])
                            raise TOONDecodeError(
                                f"Key conflict: {key!r} conflicts with nested path "
                                f"under {existing_path!r}"
                            )
                    else:
                        # Intermediate part
                        if current[part] == "LEAF":
                            # Path continues but node is already a leaf
                            existing_path = ".".join(parts[: i + 1])
                            raise TOONDecodeError(
                                f"Key conflict: {key!r} extends {existing_path!r} "
                                f"which is already a leaf key"
                            )

                        current = current[part]

    def __repr__(self) -> str:
        """Return string representation."""
        return "PathExpander()"
