"""Unit tests for TabularAnalyzer class.

This test suite covers all edge cases and behaviors of the TabularAnalyzer
including empty arrays, single elements, uniform arrays, non-uniform keys,
nested structures, and performance characteristics.
"""

import pytest

from pytoon.encoder.tabular import TabularAnalyzer


class TestTabularAnalyzerEmptyArray:
    """Test cases for empty array handling."""

    def test_empty_array_returns_true_empty_fields_zero_score(self) -> None:
        """Empty array is technically tabular but has no fields."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([])

        assert is_tabular is True
        assert fields == []
        assert score == 0.0

    def test_empty_array_tuple_structure(self) -> None:
        """Verify the return type structure."""
        analyzer = TabularAnalyzer()
        result = analyzer.analyze([])

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)
        assert isinstance(result[2], float)


class TestTabularAnalyzerSingleElement:
    """Test cases for single element arrays."""

    def test_single_dict_with_one_field(self) -> None:
        """Single dict with one field is tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}])

        assert is_tabular is True
        assert fields == ["id"]
        assert score == 100.0

    def test_single_dict_with_multiple_fields(self) -> None:
        """Single dict with multiple fields returns sorted field list."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "name": "Alice", "age": 30}])

        assert is_tabular is True
        assert fields == ["age", "id", "name"]  # Sorted alphabetically
        assert score == 100.0

    def test_single_empty_dict(self) -> None:
        """Single empty dict is tabular with no fields."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{}])

        assert is_tabular is True
        assert fields == []
        assert score == 100.0

    def test_single_dict_with_none_value(self) -> None:
        """Single dict with None value is still tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": None}])

        assert is_tabular is True
        assert fields == ["id"]
        assert score == 100.0

    def test_single_dict_with_nested_dict_not_tabular(self) -> None:
        """Single dict with nested dict is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "meta": {}}])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_single_dict_with_nested_list_not_tabular(self) -> None:
        """Single dict with nested list is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "tags": ["a", "b"]}])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0


class TestTabularAnalyzerUniformArrays:
    """Test cases for uniform arrays (all dicts with identical keys)."""

    def test_two_dicts_same_keys(self) -> None:
        """Two dicts with identical keys are tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ])

        assert is_tabular is True
        assert fields == ["id", "name"]
        assert score == 100.0

    def test_multiple_dicts_same_keys(self) -> None:
        """Multiple dicts with identical keys are tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
            {"id": 3, "name": "Charlie", "role": "user"}
        ])

        assert is_tabular is True
        assert fields == ["id", "name", "role"]
        assert score == 100.0

    def test_uniform_dicts_with_different_value_types(self) -> None:
        """Dicts with same keys but different primitive types are tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "value": "string"},
            {"id": 2, "value": 42},
            {"id": 3, "value": None},
            {"id": 4, "value": True}
        ])

        assert is_tabular is True
        assert fields == ["id", "value"]
        assert score == 100.0

    def test_field_order_is_consistent_and_sorted(self) -> None:
        """Field order should be sorted alphabetically for consistency."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"z": 1, "a": 2, "m": 3},
            {"z": 4, "a": 5, "m": 6}
        ])

        assert is_tabular is True
        assert fields == ["a", "m", "z"]
        assert score == 100.0

    def test_many_empty_dicts(self) -> None:
        """Multiple empty dicts are tabular with no fields."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{}, {}, {}])

        assert is_tabular is True
        assert fields == []
        assert score == 100.0


class TestTabularAnalyzerNonUniformKeys:
    """Test cases for arrays with non-uniform keys."""

    def test_different_key_sets_not_tabular(self) -> None:
        """Dicts with different key sets are not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1},
            {"id": 2, "name": "X"}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_subset_keys_not_tabular(self) -> None:
        """Dict with subset of keys is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob"}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_completely_different_keys_not_tabular(self) -> None:
        """Dicts with completely different keys are not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice"},
            {"age": 30, "city": "NYC"}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_empty_dict_mixed_with_non_empty_not_tabular(self) -> None:
        """Empty dict mixed with non-empty dict is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1},
            {}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_extra_key_in_one_dict_not_tabular(self) -> None:
        """Extra key in one dict makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob", "extra": "field"}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0


class TestTabularAnalyzerNestedStructures:
    """Test cases for arrays with nested dict or list values."""

    def test_nested_empty_dict_not_tabular(self) -> None:
        """Nested empty dict makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "meta": {}}])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_nested_dict_with_content_not_tabular(self) -> None:
        """Nested dict with content makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "meta": {"key": "value"}}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_nested_empty_list_not_tabular(self) -> None:
        """Nested empty list makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "tags": []}])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_nested_list_with_content_not_tabular(self) -> None:
        """Nested list with content makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "tags": ["a", "b", "c"]}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_deeply_nested_structure_not_tabular(self) -> None:
        """Deeply nested structure makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "nested": {"level1": {"level2": {}}}}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_some_values_nested_some_primitive_not_tabular(self) -> None:
        """Mix of nested and primitive values is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "name": "Alice", "meta": {}},
            {"id": 2, "name": "Bob", "meta": {}}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_nested_list_of_dicts_not_tabular(self) -> None:
        """Nested list of dicts makes array not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"id": 1, "items": [{"a": 1}]}
        ])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0


class TestTabularAnalyzerMixedTypes:
    """Test cases for arrays with non-dict elements."""

    def test_string_in_array_not_tabular(self) -> None:
        """String element in array makes it not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}, "string"])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_number_in_array_not_tabular(self) -> None:
        """Number element in array makes it not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}, 42])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_none_in_array_not_tabular(self) -> None:
        """None element in array makes it not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}, None])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_bool_in_array_not_tabular(self) -> None:
        """Boolean element in array makes it not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}, True])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_list_in_array_not_tabular(self) -> None:
        """List element in array makes it not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1}, ["a", "b"]])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_all_primitives_not_tabular(self) -> None:
        """Array of all primitives is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([1, 2, 3])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_all_strings_not_tabular(self) -> None:
        """Array of all strings is not tabular."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze(["a", "b", "c"])

        assert is_tabular is False
        assert fields == []
        assert score == 0.0


class TestTabularAnalyzerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_dict_with_numeric_string_keys(self) -> None:
        """Dict keys can be numeric strings."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"1": "a", "2": "b"},
            {"1": "c", "2": "d"}
        ])

        assert is_tabular is True
        assert fields == ["1", "2"]
        assert score == 100.0

    def test_dict_with_special_char_keys(self) -> None:
        """Dict keys with special characters are allowed."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"key-1": "a", "key_2": "b", "key.3": "c"},
            {"key-1": "d", "key_2": "e", "key.3": "f"}
        ])

        assert is_tabular is True
        assert fields == ["key-1", "key.3", "key_2"]  # Sorted
        assert score == 100.0

    def test_dict_with_unicode_keys(self) -> None:
        """Dict keys can contain unicode characters."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {"名前": "Alice", "年齢": 30},
            {"名前": "Bob", "年齢": 25}
        ])

        assert is_tabular is True
        assert fields == ["名前", "年齢"]  # Sorted by unicode
        assert score == 100.0

    def test_dict_with_very_long_keys(self) -> None:
        """Dict keys can be very long strings."""
        long_key = "x" * 1000
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {long_key: 1},
            {long_key: 2}
        ])

        assert is_tabular is True
        assert fields == [long_key]
        assert score == 100.0

    def test_values_with_various_primitive_types(self) -> None:
        """All primitive types in values are allowed."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([
            {
                "str": "text",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "none": None
            }
        ])

        assert is_tabular is True
        assert fields == ["bool", "float", "int", "none", "str"]
        assert score == 100.0


class TestTabularAnalyzerLargeArrays:
    """Test performance with large arrays."""

    def test_large_uniform_array_is_tabular(self) -> None:
        """Large uniform array should be efficiently analyzed."""
        analyzer = TabularAnalyzer()
        large_array = [{"id": i, "value": i * 2} for i in range(1000)]
        is_tabular, fields, score = analyzer.analyze(large_array)

        assert is_tabular is True
        assert fields == ["id", "value"]
        assert score == 100.0

    def test_large_array_with_many_fields(self) -> None:
        """Array with many fields per dict."""
        analyzer = TabularAnalyzer()
        fields_count = 50
        large_array = [
            {f"field_{i:02d}": j for i in range(fields_count)}
            for j in range(100)
        ]
        is_tabular, fields, score = analyzer.analyze(large_array)

        assert is_tabular is True
        assert len(fields) == fields_count
        assert score == 100.0

    def test_large_non_uniform_array_rejected_early(self) -> None:
        """Non-uniform large array should be rejected efficiently."""
        analyzer = TabularAnalyzer()
        # First element has extra key
        large_array = [{"id": i, "value": i * 2} for i in range(1000)]
        large_array[0]["extra"] = "field"

        is_tabular, fields, score = analyzer.analyze(large_array)

        assert is_tabular is False
        assert fields == []
        assert score == 0.0

    def test_large_array_with_nested_structure_rejected(self) -> None:
        """Large array with nested structure should be rejected."""
        analyzer = TabularAnalyzer()
        large_array = [{"id": i, "value": i * 2} for i in range(999)]
        large_array.append({"id": 999, "value": {"nested": "object"}})

        is_tabular, fields, score = analyzer.analyze(large_array)

        assert is_tabular is False
        assert fields == []
        assert score == 0.0


class TestTabularAnalyzerHelperMethods:
    """Test private helper methods directly."""

    def test_all_dicts_with_all_dicts(self) -> None:
        """_all_dicts returns True when all elements are dicts."""
        analyzer = TabularAnalyzer()
        assert analyzer._all_dicts([{}, {"a": 1}, {"b": 2}]) is True

    def test_all_dicts_with_non_dict(self) -> None:
        """_all_dicts returns False when any element is not a dict."""
        analyzer = TabularAnalyzer()
        assert analyzer._all_dicts([{}, "string"]) is False

    def test_uniform_keys_with_identical_sets(self) -> None:
        """_uniform_keys returns True for identical frozensets."""
        analyzer = TabularAnalyzer()
        sets = [frozenset(["a", "b"]), frozenset(["a", "b"]), frozenset(["a", "b"])]
        assert analyzer._uniform_keys(sets) is True

    def test_uniform_keys_with_different_sets(self) -> None:
        """_uniform_keys returns False for different frozensets."""
        analyzer = TabularAnalyzer()
        sets = [frozenset(["a", "b"]), frozenset(["a", "c"])]
        assert analyzer._uniform_keys(sets) is False

    def test_uniform_keys_empty_list(self) -> None:
        """_uniform_keys returns True for empty list."""
        analyzer = TabularAnalyzer()
        assert analyzer._uniform_keys([]) is True

    def test_has_nested_structures_with_nested_dict(self) -> None:
        """_has_nested_structures returns True when dict value found."""
        analyzer = TabularAnalyzer()
        array: list[dict[str, object]] = [{"id": 1, "meta": {}}]
        assert analyzer._has_nested_structures(array) is True

    def test_has_nested_structures_with_nested_list(self) -> None:
        """_has_nested_structures returns True when list value found."""
        analyzer = TabularAnalyzer()
        array: list[dict[str, object]] = [{"id": 1, "tags": []}]
        assert analyzer._has_nested_structures(array) is True

    def test_has_nested_structures_with_primitives_only(self) -> None:
        """_has_nested_structures returns False for primitive values only."""
        analyzer = TabularAnalyzer()
        array: list[dict[str, object]] = [{"id": 1, "name": "test", "value": None}]
        assert analyzer._has_nested_structures(array) is False


class TestTabularAnalyzerAcceptanceCriteria:
    """Tests directly matching the ticket acceptance criteria."""

    def test_acceptance_empty_array(self) -> None:
        """analyze([]) returns (True, [], 0.0) for empty array."""
        analyzer = TabularAnalyzer()
        result = analyzer.analyze([])
        assert result == (True, [], 0.0)

    def test_acceptance_single_element(self) -> None:
        """analyze([{"id": 1}]) returns (True, ["id"], 100.0)."""
        analyzer = TabularAnalyzer()
        result = analyzer.analyze([{"id": 1}])
        assert result == (True, ["id"], 100.0)

    def test_acceptance_non_uniform_keys(self) -> None:
        """analyze([{"id": 1}, {"id": 2, "name": "X"}]) returns (False, [], 0.0)."""
        analyzer = TabularAnalyzer()
        result = analyzer.analyze([{"id": 1}, {"id": 2, "name": "X"}])
        assert result == (False, [], 0.0)

    def test_acceptance_nested_object(self) -> None:
        """analyze([{"id": 1, "meta": {}}]) returns (False, ..., 0.0)."""
        analyzer = TabularAnalyzer()
        is_tabular, fields, score = analyzer.analyze([{"id": 1, "meta": {}}])
        assert is_tabular is False
        assert score == 0.0

    def test_acceptance_field_order_consistency(self) -> None:
        """Returns field list in consistent order."""
        analyzer = TabularAnalyzer()
        # Test with same data multiple times
        for _ in range(10):
            is_tabular, fields, score = analyzer.analyze([
                {"z": 1, "a": 2, "m": 3},
                {"z": 4, "a": 5, "m": 6}
            ])
            assert fields == ["a", "m", "z"]  # Always sorted


class TestTabularAnalyzerComplexityBehavior:
    """Tests to verify O(n*m) time complexity behavior."""

    def test_time_complexity_scales_with_array_length(self) -> None:
        """Time should scale linearly with array length."""
        analyzer = TabularAnalyzer()

        # Small array
        small = [{"a": 1, "b": 2} for _ in range(10)]
        result_small = analyzer.analyze(small)
        assert result_small[0] is True

        # Medium array
        medium = [{"a": 1, "b": 2} for _ in range(100)]
        result_medium = analyzer.analyze(medium)
        assert result_medium[0] is True

        # Large array
        large = [{"a": 1, "b": 2} for _ in range(1000)]
        result_large = analyzer.analyze(large)
        assert result_large[0] is True

    def test_time_complexity_scales_with_field_count(self) -> None:
        """Time should scale linearly with field count."""
        analyzer = TabularAnalyzer()

        # Few fields
        few_fields = [{f"f{i}": i for i in range(5)} for _ in range(10)]
        result_few = analyzer.analyze(few_fields)
        assert result_few[0] is True

        # Many fields
        many_fields = [{f"f{i}": i for i in range(50)} for _ in range(10)]
        result_many = analyzer.analyze(many_fields)
        assert result_many[0] is True

        # Very many fields
        very_many = [{f"f{i}": i for i in range(200)} for _ in range(10)]
        result_very = analyzer.analyze(very_many)
        assert result_very[0] is True
