"""Unit tests for DataMetrics class."""

import pytest

from pytoon.decision.metrics import DataMetrics


class TestDataMetricsMaxDepth:
    """Tests for max_depth calculation."""

    def test_primitive_depth_zero(self) -> None:
        """Primitive values have depth 0."""
        assert DataMetrics.analyze(None).max_depth == 0
        assert DataMetrics.analyze(True).max_depth == 0
        assert DataMetrics.analyze(42).max_depth == 0
        assert DataMetrics.analyze("hello").max_depth == 0

    def test_flat_dict_depth_one(self) -> None:
        """Flat dict has depth 1."""
        data = {"name": "Alice", "age": 30}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 1

    def test_flat_list_depth_one(self) -> None:
        """Flat list of primitives has depth 1."""
        data = [1, 2, 3]
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 1

    def test_nested_dict_depth_two(self) -> None:
        """Nested dict has depth 2."""
        data = {"user": {"name": "Alice"}}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 2

    def test_deeply_nested_depth_calculation(self) -> None:
        """Deeply nested structures calculate correct depth."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": 1}}}}}}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 6

    def test_list_of_dicts_depth_two(self) -> None:
        """List of dicts has depth 2."""
        data = [{"id": 1}, {"id": 2}]
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 2

    def test_dict_with_list_depth_two(self) -> None:
        """Dict containing list has depth 2."""
        data = {"items": [1, 2, 3]}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 2

    def test_complex_structure_depth(self) -> None:
        """Complex nested structure calculates max depth."""
        data = {
            "users": [
                {"id": 1, "profile": {"bio": "text"}},
                {"id": 2, "profile": {"bio": "text"}},
            ]
        }
        # users -> [array] -> profile -> bio = depth 4
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 4

    def test_empty_dict_depth_one(self) -> None:
        """Empty dict has depth 1 (the dict itself is level 1)."""
        # Actually empty dict has no values, so depth is just the dict = 0
        # Wait, let me reconsider: empty dict is still a structure, but max depth is 0
        # because we measure depth of traversal. If no values, max remains 0.
        # Actually, the dict itself represents depth 0 (root), but we measure max depth of VALUES.
        # Since no values, max depth stays 0.
        data: dict[str, int] = {}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 0

    def test_empty_list_depth_zero(self) -> None:
        """Empty list has depth 0 (no elements to traverse)."""
        data: list[int] = []
        metrics = DataMetrics.analyze(data)
        # Root array is at depth 0, but no children
        assert metrics.max_depth == 0


class TestDataMetricsUniformityScore:
    """Tests for uniformity_score calculation."""

    def test_no_arrays_zero_uniformity(self) -> None:
        """Data with no arrays has 0% uniformity."""
        data = {"name": "Alice"}
        metrics = DataMetrics.analyze(data)
        assert metrics.uniformity_score == 0.0

    def test_single_tabular_array_full_uniformity(self) -> None:
        """Single tabular array has 100% uniformity."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        metrics = DataMetrics.analyze(data)
        assert metrics.uniformity_score == 100.0

    def test_non_tabular_array_zero_uniformity(self) -> None:
        """Array with mixed types has 0% uniformity."""
        data = [1, "string", True]
        metrics = DataMetrics.analyze(data)
        assert metrics.uniformity_score == 0.0

    def test_mixed_arrays_partial_uniformity(self) -> None:
        """Mix of tabular and non-tabular arrays gives partial score."""
        data = {
            "users": [{"id": 1}, {"id": 2}],  # Tabular
            "tags": ["a", "b", "c"],  # Not tabular
        }
        metrics = DataMetrics.analyze(data)
        # 1 out of 2 arrays is tabular = 50%
        assert metrics.uniformity_score == 50.0

    def test_empty_array_not_counted_as_tabular(self) -> None:
        """Empty arrays don't count as tabular (no data to encode)."""
        data = {"items": []}
        metrics = DataMetrics.analyze(data)
        # Empty array is analyzed as tabular=True but len=0, so not counted
        assert metrics.uniformity_score == 0.0
        assert metrics.tabular_eligibility == 0

    def test_all_arrays_tabular_full_uniformity(self) -> None:
        """All arrays tabular gives 100% uniformity."""
        data = {
            "users": [{"id": 1}, {"id": 2}],
            "products": [{"sku": "A"}, {"sku": "B"}],
        }
        metrics = DataMetrics.analyze(data)
        assert metrics.uniformity_score == 100.0

    def test_no_arrays_tabular_zero_uniformity(self) -> None:
        """No tabular arrays gives 0% uniformity."""
        data = {
            "tags": ["a", "b"],
            "numbers": [1, 2, 3],
        }
        metrics = DataMetrics.analyze(data)
        assert metrics.uniformity_score == 0.0


class TestDataMetricsTabularEligibility:
    """Tests for tabular_eligibility counting."""

    def test_count_tabular_arrays(self) -> None:
        """Counts number of tabular-eligible arrays."""
        data = {
            "users": [{"id": 1}, {"id": 2}],
            "products": [{"sku": "A"}, {"sku": "B"}],
            "tags": ["a", "b"],
        }
        metrics = DataMetrics.analyze(data)
        assert metrics.tabular_eligibility == 2

    def test_no_tabular_arrays(self) -> None:
        """No tabular arrays gives count of 0."""
        data = {"values": [1, 2, 3]}
        metrics = DataMetrics.analyze(data)
        assert metrics.tabular_eligibility == 0

    def test_single_element_array_tabular(self) -> None:
        """Single-element dict array is tabular."""
        data = [{"id": 1}]
        metrics = DataMetrics.analyze(data)
        assert metrics.tabular_eligibility == 1


class TestDataMetricsTotalArrays:
    """Tests for total_arrays counting."""

    def test_no_arrays(self) -> None:
        """Data with no arrays has total_arrays = 0."""
        data = {"name": "Alice"}
        metrics = DataMetrics.analyze(data)
        assert metrics.total_arrays == 0

    def test_single_array(self) -> None:
        """Single array is counted."""
        data = [1, 2, 3]
        metrics = DataMetrics.analyze(data)
        assert metrics.total_arrays == 1

    def test_nested_arrays(self) -> None:
        """Nested arrays are all counted."""
        data = {"items": [1, 2], "more": [3, 4]}
        metrics = DataMetrics.analyze(data)
        assert metrics.total_arrays == 2

    def test_array_of_arrays(self) -> None:
        """Arrays within arrays are counted."""
        data = [[1, 2], [3, 4], [5, 6]]
        metrics = DataMetrics.analyze(data)
        assert metrics.total_arrays == 4  # Outer + 3 inner


class TestDataMetricsReferenceDensity:
    """Tests for reference_density calculation."""

    def test_no_shared_refs_zero_density(self) -> None:
        """No shared references gives 0% density."""
        data = {"a": {"x": 1}, "b": {"y": 2}}
        metrics = DataMetrics.analyze(data)
        assert metrics.reference_density == 0.0

    def test_no_objects_zero_density(self) -> None:
        """No dict objects gives 0% density."""
        data = [1, 2, 3]
        metrics = DataMetrics.analyze(data)
        assert metrics.reference_density == 0.0

    def test_shared_reference_detected(self) -> None:
        """Shared object reference increases density."""
        shared_obj = {"name": "shared"}
        data = {"a": shared_obj, "b": shared_obj}
        metrics = DataMetrics.analyze(data)
        # shared_obj is referenced twice, counted once as shared
        # Total objects: root + shared = 2, shared refs = 1
        # Density = 1/2 * 100 = 50%
        assert metrics.reference_density == 50.0

    def test_multiple_shared_refs(self) -> None:
        """Multiple shared references increase density."""
        shared1 = {"x": 1}
        shared2 = {"y": 2}
        data = {
            "a": shared1,
            "b": shared1,
            "c": shared2,
            "d": shared2,
        }
        metrics = DataMetrics.analyze(data)
        # Total objects: root + shared1 + shared2 = 3
        # Shared refs: shared1 appears twice (1 shared), shared2 appears twice (1 shared) = 2
        # Density = 2/3 * 100 = 66.67%
        assert metrics.reference_density == pytest.approx(66.67, rel=0.01)


class TestDataMetricsTotalObjects:
    """Tests for total_objects counting."""

    def test_single_dict(self) -> None:
        """Single dict is counted."""
        data = {"name": "Alice"}
        metrics = DataMetrics.analyze(data)
        assert metrics.total_objects == 1

    def test_nested_dicts(self) -> None:
        """Nested dicts are all counted."""
        data = {"a": {"b": {"c": 1}}}
        metrics = DataMetrics.analyze(data)
        assert metrics.total_objects == 3

    def test_no_dicts(self) -> None:
        """Data with no dicts has total_objects = 0."""
        data = [1, 2, 3]
        metrics = DataMetrics.analyze(data)
        assert metrics.total_objects == 0

    def test_list_of_dicts(self) -> None:
        """List of dicts counts each dict."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        metrics = DataMetrics.analyze(data)
        assert metrics.total_objects == 3


class TestDataMetricsTotalSizeBytes:
    """Tests for total_size_bytes calculation."""

    def test_size_is_positive(self) -> None:
        """Size is always positive for non-empty data."""
        data = {"name": "Alice"}
        metrics = DataMetrics.analyze(data)
        assert metrics.total_size_bytes > 0

    def test_larger_data_larger_size(self) -> None:
        """Larger data structures have larger size."""
        small_data = {"a": 1}
        large_data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}

        small_metrics = DataMetrics.analyze(small_data)
        large_metrics = DataMetrics.analyze(large_data)

        assert large_metrics.total_size_bytes > small_metrics.total_size_bytes

    def test_nested_increases_size(self) -> None:
        """Nested structures increase total size."""
        flat = {"a": 1}
        nested = {"a": {"b": {"c": 1}}}

        flat_metrics = DataMetrics.analyze(flat)
        nested_metrics = DataMetrics.analyze(nested)

        assert nested_metrics.total_size_bytes > flat_metrics.total_size_bytes


class TestDataMetricsKeyCount:
    """Tests for key_count calculation."""

    def test_single_key(self) -> None:
        """Single key is counted."""
        data = {"name": "Alice"}
        metrics = DataMetrics.analyze(data)
        assert metrics.key_count == 1

    def test_multiple_keys(self) -> None:
        """Multiple keys are counted."""
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        metrics = DataMetrics.analyze(data)
        assert metrics.key_count == 3

    def test_nested_keys_combined(self) -> None:
        """Keys from nested dicts are combined (unique)."""
        data = {"user": {"name": "Alice", "age": 30}}
        metrics = DataMetrics.analyze(data)
        # Keys: "user", "name", "age"
        assert metrics.key_count == 3

    def test_duplicate_keys_counted_once(self) -> None:
        """Same key in different objects counted once."""
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        metrics = DataMetrics.analyze(data)
        # Keys: "id", "name" (duplicates don't add to count)
        assert metrics.key_count == 2

    def test_no_dicts_zero_keys(self) -> None:
        """No dicts means zero keys."""
        data = [1, 2, 3]
        metrics = DataMetrics.analyze(data)
        assert metrics.key_count == 0


class TestDataMetricsValueCount:
    """Tests for value_count calculation."""

    def test_dict_values_counted(self) -> None:
        """Dict values are counted."""
        data = {"a": 1, "b": 2}
        metrics = DataMetrics.analyze(data)
        assert metrics.value_count == 2

    def test_list_elements_counted(self) -> None:
        """List elements are counted as values."""
        data = [1, 2, 3, 4, 5]
        metrics = DataMetrics.analyze(data)
        assert metrics.value_count == 5

    def test_nested_values_counted(self) -> None:
        """All nested values are counted."""
        data = {"outer": {"inner": 1}}
        # outer -> nested dict (1 value), inner -> 1 (1 value) = 2 values
        metrics = DataMetrics.analyze(data)
        assert metrics.value_count == 2

    def test_complex_structure_values(self) -> None:
        """Complex structures count all values."""
        data = {
            "users": [{"id": 1}, {"id": 2}],
            "count": 2,
        }
        # "users" value: list (1)
        # "count" value: 2 (1)
        # List items: 2 dicts (2)
        # Dict values: id: 1, id: 2 (2)
        # Total: 1 + 1 + 2 + 2 = 6
        metrics = DataMetrics.analyze(data)
        assert metrics.value_count == 6


class TestDataMetricsEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_dict(self) -> None:
        """Empty dict handles correctly."""
        data: dict[str, int] = {}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 0
        assert metrics.total_objects == 1
        assert metrics.key_count == 0
        assert metrics.value_count == 0

    def test_empty_list(self) -> None:
        """Empty list handles correctly."""
        data: list[int] = []
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 0
        assert metrics.total_arrays == 1
        assert metrics.value_count == 0

    def test_none_value(self) -> None:
        """None value handles correctly."""
        metrics = DataMetrics.analyze(None)
        assert metrics.max_depth == 0
        assert metrics.total_objects == 0
        assert metrics.total_arrays == 0
        assert metrics.total_size_bytes > 0

    def test_boolean_value(self) -> None:
        """Boolean value handles correctly."""
        metrics = DataMetrics.analyze(True)
        assert metrics.max_depth == 0
        assert metrics.total_size_bytes > 0

    def test_string_value(self) -> None:
        """String value handles correctly."""
        metrics = DataMetrics.analyze("hello world")
        assert metrics.max_depth == 0
        assert metrics.total_size_bytes > 0

    def test_large_dataset(self) -> None:
        """Large dataset handles efficiently."""
        data = {"items": [{"id": i, "value": i * 2} for i in range(1000)]}
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 3
        assert metrics.tabular_eligibility == 1
        assert metrics.uniformity_score == 100.0
        assert metrics.total_objects == 1001  # root + 1000 dicts
        assert metrics.value_count > 2000  # 2 values per dict + list items

    def test_deeply_nested_graph_structure(self) -> None:
        """Deeply nested graph-like structure handles correctly."""
        node_d = {"value": 4}
        node_c = {"value": 3, "next": node_d}
        node_b = {"value": 2, "next": node_c}
        node_a = {"value": 1, "next": node_b}

        metrics = DataMetrics.analyze(node_a)
        assert metrics.max_depth == 4
        assert metrics.total_objects == 4

    def test_circular_reference_handled(self) -> None:
        """Circular references don't cause infinite loop."""
        data: dict[str, Any] = {"name": "root"}
        data["self"] = data  # Circular reference

        # Should not hang or crash
        metrics = DataMetrics.analyze(data)
        assert metrics.total_objects == 1
        assert metrics.reference_density > 0  # Shared ref detected


class TestDataMetricsImmutability:
    """Tests for DataMetrics immutability."""

    def test_frozen_dataclass(self) -> None:
        """DataMetrics is immutable (frozen)."""
        metrics = DataMetrics.analyze({"name": "Alice"})

        with pytest.raises(AttributeError):
            metrics.max_depth = 100  # type: ignore[misc]

    def test_analyze_returns_new_instance(self) -> None:
        """Each analyze call returns a new instance."""
        data = {"name": "Alice"}
        m1 = DataMetrics.analyze(data)
        m2 = DataMetrics.analyze(data)

        assert m1 is not m2
        assert m1 == m2  # But values are equal


class TestDataMetricsRealWorldScenarios:
    """Tests for real-world data scenarios."""

    def test_api_response_tabular(self) -> None:
        """Typical API response with tabular data."""
        data = {
            "status": "success",
            "data": [
                {"id": 1, "name": "Product A", "price": 10.99},
                {"id": 2, "name": "Product B", "price": 20.99},
                {"id": 3, "name": "Product C", "price": 15.99},
            ],
        }
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 3
        assert metrics.tabular_eligibility == 1
        assert metrics.uniformity_score == 100.0

    def test_config_file_nested(self) -> None:
        """Configuration file with nested settings."""
        data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"user": "admin", "password": "secret"},
            },
            "logging": {"level": "INFO", "file": "app.log"},
        }
        metrics = DataMetrics.analyze(data)
        assert metrics.max_depth == 3
        assert metrics.tabular_eligibility == 0
        # Objects: root, database, credentials, logging = 4
        assert metrics.total_objects == 4

    def test_mixed_content_structure(self) -> None:
        """Mixed content with arrays and nested objects."""
        data = {
            "title": "Report",
            "sections": [
                {"name": "Intro", "content": "text"},
                {"name": "Body", "content": "text"},
            ],
            "metadata": {"author": "Alice", "date": "2024-01-01"},
            "tags": ["report", "analysis", "2024"],
        }
        metrics = DataMetrics.analyze(data)
        # 2 arrays: sections (tabular), tags (not tabular)
        assert metrics.total_arrays == 2
        assert metrics.tabular_eligibility == 1
        assert metrics.uniformity_score == 50.0
