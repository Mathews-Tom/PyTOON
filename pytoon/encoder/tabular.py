"""TabularAnalyzer class for PyToon encoder.

This module provides functionality to analyze arrays and determine if they
qualify for TOON's efficient tabular encoding format.
"""

from typing import Any


class TabularAnalyzer:
    """Analyzes arrays to determine tabular format eligibility.

    The TabularAnalyzer examines arrays to check if they can be encoded
    in TOON's space-efficient tabular format. Arrays qualify for tabular
    encoding when:

    1. All elements are dictionaries
    2. All dictionaries have identical key sets
    3. No dictionary values contain nested structures (dicts or lists)

    Examples:
        >>> analyzer = TabularAnalyzer()
        >>> analyzer.analyze([])
        (True, [], 0.0)

        >>> analyzer.analyze([{"id": 1, "name": "Alice"}])
        (True, ['id', 'name'], 100.0)

        >>> analyzer.analyze([{"id": 1}, {"id": 2, "name": "X"}])
        (False, [], 0.0)

        >>> analyzer.analyze([{"id": 1, "meta": {}}])
        (False, [], 0.0)
    """

    def analyze(self, array: list[Any]) -> tuple[bool, list[str], float]:
        """Analyze an array to determine tabular format eligibility.

        Args:
            array: A list of any Python objects to analyze.

        Returns:
            A tuple containing:
                - is_tabular: True if the array can be encoded in tabular format
                - field_names: List of field names in sorted order (empty if not tabular)
                - uniformity_score: Percentage of dicts with matching key set (0.0-100.0)

        Examples:
            >>> analyzer = TabularAnalyzer()

            Empty array (valid but no fields):
            >>> analyzer.analyze([])
            (True, [], 0.0)

            Single element array:
            >>> analyzer.analyze([{"id": 1}])
            (True, ['id'], 100.0)

            Uniform array with multiple elements:
            >>> analyzer.analyze([{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
            (True, ['id', 'name'], 100.0)

            Non-uniform keys:
            >>> analyzer.analyze([{"id": 1}, {"id": 2, "name": "X"}])
            (False, [], 0.0)

            Nested dict (not allowed):
            >>> analyzer.analyze([{"id": 1, "meta": {}}])
            (False, [], 0.0)

            Nested list (not allowed):
            >>> analyzer.analyze([{"id": 1, "tags": ["a", "b"]}])
            (False, [], 0.0)

            Mixed types (not all dicts):
            >>> analyzer.analyze([{"id": 1}, "string", 42])
            (False, [], 0.0)
        """
        # Handle empty array case
        if not array:
            return (True, [], 0.0)

        # Check if all elements are dictionaries
        if not self._all_dicts(array):
            return (False, [], 0.0)

        # Get field sets for all dictionaries
        field_sets = [frozenset(obj.keys()) for obj in array]

        # Check if all dictionaries have identical key sets
        if not self._uniform_keys(field_sets):
            return (False, [], 0.0)

        # Get common fields (sorted for consistent ordering)
        common_fields = sorted(field_sets[0])

        # Check for nested structures in values
        if self._has_nested_structures(array):
            return (False, [], 0.0)

        # All checks passed - array is tabular
        return (True, common_fields, 100.0)

    def _all_dicts(self, array: list[Any]) -> bool:
        """Check if all elements in the array are dictionaries.

        Args:
            array: A non-empty list of objects.

        Returns:
            True if all elements are dict instances, False otherwise.
        """
        return all(isinstance(obj, dict) for obj in array)

    def _uniform_keys(self, field_sets: list[frozenset[Any]]) -> bool:
        """Check if all field sets are identical.

        Args:
            field_sets: List of frozensets containing dictionary keys.

        Returns:
            True if all field sets are identical, False otherwise.
        """
        if not field_sets:
            return True

        first_set = field_sets[0]
        return all(field_set == first_set for field_set in field_sets)

    def _has_nested_structures(self, array: list[dict[Any, Any]]) -> bool:
        """Check if any dictionary value contains nested structures.

        Args:
            array: A list of dictionaries to check.

        Returns:
            True if any value is a dict or list, False otherwise.
        """
        for obj in array:
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    return True
        return False
