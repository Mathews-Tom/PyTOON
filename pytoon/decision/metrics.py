"""DataMetrics class for computing structural analysis of Python data.

This module provides functionality to analyze data structures and compute
metrics that inform format selection decisions.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from pytoon.encoder.tabular import TabularAnalyzer


@dataclass(frozen=True)
class DataMetrics:
    """Container for computed structural metrics of data.

    All metrics are computed during initialization via analyze() class method.

    Attributes:
        max_depth: Maximum nesting depth in object tree.
        uniformity_score: Percentage of arrays eligible for tabular format (0.0-100.0).
        tabular_eligibility: Number of arrays that qualify for tabular encoding.
        total_arrays: Total number of arrays in the data structure.
        reference_density: Percentage of potential reference relationships (0.0-100.0).
        total_objects: Total number of dict objects in the data.
        total_size_bytes: Approximate size of data structure in bytes.
        key_count: Total number of unique keys across all objects.
        value_count: Total number of values in the data structure.

    Examples:
        >>> from pytoon.decision.metrics import DataMetrics
        >>> data = {"name": "Alice", "age": 30}
        >>> metrics = DataMetrics.analyze(data)
        >>> metrics.max_depth
        1
        >>> metrics.uniformity_score
        0.0
    """

    max_depth: int
    uniformity_score: float
    tabular_eligibility: int
    total_arrays: int
    reference_density: float
    total_objects: int
    total_size_bytes: int
    key_count: int
    value_count: int

    @classmethod
    def analyze(cls, data: Any) -> DataMetrics:
        """Analyze data structure and compute all metrics.

        Performs a single O(n) traversal to compute all structural metrics.

        Args:
            data: Any Python object to analyze (dict, list, or primitive).

        Returns:
            DataMetrics instance with all computed metrics.

        Examples:
            >>> metrics = DataMetrics.analyze({"users": [{"id": 1}, {"id": 2}]})
            >>> metrics.max_depth
            3
            >>> metrics.uniformity_score
            100.0

            >>> metrics = DataMetrics.analyze([1, 2, 3])
            >>> metrics.total_arrays
            1
            >>> metrics.tabular_eligibility
            0

            >>> metrics = DataMetrics.analyze({"a": {"b": {"c": 1}}})
            >>> metrics.max_depth
            3
        """
        analyzer = _MetricsAnalyzer()
        return analyzer.compute(data)


class _MetricsAnalyzer:
    """Internal helper class for computing metrics in a single traversal.

    Uses O(n) traversal with tracking of visited objects to handle
    circular references and compute all metrics efficiently.
    """

    def __init__(self) -> None:
        """Initialize the metrics analyzer."""
        self._visited: set[int] = set()
        self._max_depth: int = 0
        self._arrays: list[list[Any]] = []
        self._object_ids: set[int] = set()
        self._shared_refs: int = 0
        self._total_objects: int = 0
        self._total_size: int = 0
        self._all_keys: set[str] = set()
        self._value_count: int = 0
        self._tabular_analyzer = TabularAnalyzer()

    def compute(self, data: Any) -> DataMetrics:
        """Compute all metrics for the given data.

        Args:
            data: Python object to analyze.

        Returns:
            DataMetrics instance with computed values.
        """
        # Perform traversal
        self._traverse(data, depth=0)

        # Calculate uniformity score
        uniformity_score = self._calculate_uniformity_score()

        # Calculate tabular eligibility count
        tabular_eligibility = self._calculate_tabular_eligibility()

        # Calculate reference density
        reference_density = self._calculate_reference_density()

        return DataMetrics(
            max_depth=self._max_depth,
            uniformity_score=uniformity_score,
            tabular_eligibility=tabular_eligibility,
            total_arrays=len(self._arrays),
            reference_density=reference_density,
            total_objects=self._total_objects,
            total_size_bytes=self._total_size,
            key_count=len(self._all_keys),
            value_count=self._value_count,
        )

    def _traverse(self, obj: Any, depth: int) -> None:
        """Recursively traverse data structure collecting metrics.

        Args:
            obj: Current object being traversed.
            depth: Current nesting depth.
        """
        # Update max depth
        if depth > self._max_depth:
            self._max_depth = depth

        # Track size
        self._total_size += sys.getsizeof(obj)

        # Check for shared references (by object id)
        if isinstance(obj, (dict, list)):
            obj_id = id(obj)
            if obj_id in self._object_ids:
                self._shared_refs += 1
                return  # Don't traverse again (circular reference protection)
            self._object_ids.add(obj_id)

        if isinstance(obj, dict):
            self._total_objects += 1
            self._all_keys.update(obj.keys())
            for value in obj.values():
                self._value_count += 1
                self._traverse(value, depth + 1)

        elif isinstance(obj, list):
            self._arrays.append(obj)
            for item in obj:
                self._value_count += 1
                self._traverse(item, depth + 1)

        else:
            # Primitive value - no further traversal needed
            pass

    def _calculate_uniformity_score(self) -> float:
        """Calculate percentage of arrays eligible for tabular format.

        Returns:
            Uniformity score from 0.0 to 100.0.
        """
        if not self._arrays:
            return 0.0

        tabular_count = 0
        for array in self._arrays:
            is_tabular, _, _ = self._tabular_analyzer.analyze(array)
            if is_tabular and len(array) > 0:
                tabular_count += 1

        return (tabular_count / len(self._arrays)) * 100.0

    def _calculate_tabular_eligibility(self) -> int:
        """Count number of arrays eligible for tabular encoding.

        Returns:
            Number of arrays that qualify for tabular format.
        """
        count = 0
        for array in self._arrays:
            is_tabular, _, _ = self._tabular_analyzer.analyze(array)
            if is_tabular and len(array) > 0:
                count += 1
        return count

    def _calculate_reference_density(self) -> float:
        """Calculate percentage of potential reference relationships.

        Based on shared object references (same object id appearing multiple times).

        Returns:
            Reference density from 0.0 to 100.0.
        """
        if self._total_objects == 0:
            return 0.0

        # Density is based on shared refs vs total objects
        return (self._shared_refs / self._total_objects) * 100.0
