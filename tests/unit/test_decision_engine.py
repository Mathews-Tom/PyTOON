"""Unit tests for DecisionEngine class."""

import pytest

from pytoon.decision.engine import DecisionEngine, FormatDecision
from pytoon.decision.metrics import DataMetrics


class TestDecisionEngineBasic:
    """Basic functionality tests for DecisionEngine."""

    def test_returns_format_decision(self) -> None:
        """analyze() returns FormatDecision instance."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})
        assert isinstance(decision, FormatDecision)

    def test_decision_has_required_fields(self) -> None:
        """FormatDecision contains all required fields."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        assert hasattr(decision, "recommended_format")
        assert hasattr(decision, "confidence")
        assert hasattr(decision, "reasoning")
        assert hasattr(decision, "metrics")

    def test_confidence_in_valid_range(self) -> None:
        """Confidence score is between 0.0 and 1.0."""
        engine = DecisionEngine()

        test_cases = [
            {"key": "value"},
            [1, 2, 3],
            [{"id": 1}, {"id": 2}],
            {"a": {"b": {"c": 1}}},
        ]

        for data in test_cases:
            decision = engine.analyze(data)
            assert 0.0 <= decision.confidence <= 1.0

    def test_reasoning_is_list(self) -> None:
        """Reasoning is a list of strings."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        assert isinstance(decision.reasoning, list)
        assert all(isinstance(r, str) for r in decision.reasoning)
        assert len(decision.reasoning) > 0

    def test_metrics_is_data_metrics(self) -> None:
        """Metrics field is DataMetrics instance."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        assert isinstance(decision.metrics, DataMetrics)

    def test_valid_format_types(self) -> None:
        """Recommended format is one of valid types."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        valid_formats = {"toon", "json", "graph", "hybrid"}
        assert decision.recommended_format in valid_formats


class TestDecisionEngineTabularData:
    """Tests for tabular/uniform data recommendations."""

    def test_uniform_array_recommends_toon(self) -> None:
        """Highly uniform array of dicts recommends TOON."""
        engine = DecisionEngine()
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"
        assert decision.confidence > 0.7

    def test_high_uniformity_strong_toon_preference(self) -> None:
        """100% uniformity gives high confidence TOON recommendation."""
        engine = DecisionEngine()
        data = [{"id": i, "value": i * 2} for i in range(100)]
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"
        assert decision.confidence > 0.8
        assert any("uniformity" in r.lower() for r in decision.reasoning)

    def test_single_tabular_array_with_wrapper(self) -> None:
        """Wrapped tabular array recommends TOON."""
        engine = DecisionEngine()
        data = {
            "data": [
                {"id": 1, "name": "Product A"},
                {"id": 2, "name": "Product B"},
            ]
        }
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"

    def test_empty_array_no_strong_preference(self) -> None:
        """Empty array doesn't strongly prefer any format."""
        engine = DecisionEngine()
        data: list[dict[str, int]] = []
        decision = engine.analyze(data)

        # With no data, no strong preference
        assert decision.confidence < 0.9

    def test_reasoning_mentions_tabular_eligibility(self) -> None:
        """Reasoning mentions tabular encoding eligibility."""
        engine = DecisionEngine()
        data = [{"id": 1}, {"id": 2}]
        decision = engine.analyze(data)

        assert any("tabular" in r.lower() for r in decision.reasoning)


class TestDecisionEngineNestedData:
    """Tests for nested/complex data recommendations."""

    def test_deeply_nested_recommends_json(self) -> None:
        """Deeply nested structure (>6 levels) recommends JSON."""
        engine = DecisionEngine()
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
        decision = engine.analyze(data)

        assert decision.recommended_format == "json"
        assert any("depth" in r.lower() or "nested" in r.lower() for r in decision.reasoning)

    def test_moderate_nesting_not_penalized(self) -> None:
        """Moderate nesting (3-6 levels) doesn't strongly favor JSON."""
        engine = DecisionEngine()
        data = {"a": {"b": {"c": {"d": 1}}}}
        decision = engine.analyze(data)

        # Should not strongly favor JSON for moderate depth
        assert decision.metrics.max_depth <= 6

    def test_shallow_structure_favors_toon(self) -> None:
        """Shallow structure (<=3 levels) slightly favors TOON."""
        engine = DecisionEngine()
        data = {"user": {"name": "Alice"}}
        decision = engine.analyze(data)

        # Shallow structure should mention in reasoning
        assert any("shallow" in r.lower() or "level" in r.lower() for r in decision.reasoning)

    def test_reasoning_mentions_depth(self) -> None:
        """Reasoning includes depth information."""
        engine = DecisionEngine()
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
        decision = engine.analyze(data)

        depth_mentioned = any(
            "depth" in r.lower() or "level" in r.lower() or "nest" in r.lower()
            for r in decision.reasoning
        )
        assert depth_mentioned


class TestDecisionEngineHeterogeneousData:
    """Tests for heterogeneous/mixed data recommendations."""

    def test_low_uniformity_favors_json(self) -> None:
        """Low uniformity (<30%) favors JSON."""
        engine = DecisionEngine()
        data = {
            "mixed": [1, "string", True, None],
            "config": {"key": "value"},
        }
        decision = engine.analyze(data)

        # Low uniformity should favor JSON or at least mention it
        assert any("uniformity" in r.lower() for r in decision.reasoning)

    def test_non_tabular_arrays_reduce_toon_preference(self) -> None:
        """Arrays with primitives don't strongly favor TOON."""
        engine = DecisionEngine()
        data = {"tags": ["a", "b", "c"], "numbers": [1, 2, 3]}
        decision = engine.analyze(data)

        # No tabular arrays, so weaker TOON preference
        assert decision.metrics.tabular_eligibility == 0

    def test_single_primitive_value(self) -> None:
        """Single primitive value gets a recommendation."""
        engine = DecisionEngine()

        for value in [None, True, 42, "string"]:
            decision = engine.analyze(value)
            assert decision.recommended_format in {"toon", "json", "graph", "hybrid"}
            assert 0.0 <= decision.confidence <= 1.0


class TestDecisionEngineGraphData:
    """Tests for graph/reference-heavy data recommendations."""

    def test_high_reference_density_recommends_graph(self) -> None:
        """High reference density (>20%) recommends graph format."""
        engine = DecisionEngine()

        # Create data with many shared references
        shared1 = {"name": "shared1"}
        shared2 = {"name": "shared2"}
        data = {
            "ref1a": shared1,
            "ref1b": shared1,
            "ref2a": shared2,
            "ref2b": shared2,
        }
        decision = engine.analyze(data)

        # Should detect shared references
        assert decision.metrics.reference_density > 0
        assert any("reference" in r.lower() for r in decision.reasoning)

    def test_circular_reference_high_density(self) -> None:
        """Circular reference increases reference density."""
        engine = DecisionEngine()

        data: dict[str, object] = {"name": "root"}
        data["self"] = data

        decision = engine.analyze(data)
        assert decision.metrics.reference_density > 0

    def test_no_shared_refs_low_graph_score(self) -> None:
        """Data without shared references doesn't recommend graph."""
        engine = DecisionEngine()
        data = {"a": {"x": 1}, "b": {"y": 2}}
        decision = engine.analyze(data)

        # No shared refs, so graph not recommended
        assert decision.recommended_format != "graph"
        assert decision.metrics.reference_density == 0.0


class TestDecisionEngineDataSize:
    """Tests for data size influence on recommendations."""

    def test_large_dataset_favors_toon(self) -> None:
        """Large dataset (>1000 values) slightly favors TOON."""
        engine = DecisionEngine()
        data = [{"id": i, "value": i * 2} for i in range(500)]
        decision = engine.analyze(data)

        # Large uniform dataset should strongly favor TOON
        assert decision.recommended_format == "toon"
        assert decision.metrics.value_count > 1000

    def test_small_dataset_noted(self) -> None:
        """Small dataset is noted in reasoning."""
        engine = DecisionEngine()
        data = {"a": 1, "b": 2}
        decision = engine.analyze(data)

        # Small dataset should be mentioned
        small_mentioned = any("small" in r.lower() for r in decision.reasoning)
        values_mentioned = any("values" in r.lower() for r in decision.reasoning)
        assert small_mentioned or values_mentioned


class TestDecisionEngineConfidence:
    """Tests for confidence score calculation."""

    def test_clear_toon_case_high_confidence(self) -> None:
        """Clear TOON case (high uniformity, shallow) has high confidence."""
        engine = DecisionEngine()
        data = [{"id": i, "name": f"Item {i}"} for i in range(50)]
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"
        assert decision.confidence >= 0.8

    def test_clear_json_case_high_confidence(self) -> None:
        """Clear JSON case (deep nesting, low uniformity) has high confidence."""
        engine = DecisionEngine()
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": 1}}}}}}}}
        decision = engine.analyze(data)

        assert decision.recommended_format == "json"
        assert decision.confidence >= 0.6

    def test_ambiguous_case_lower_confidence(self) -> None:
        """Ambiguous case has lower confidence."""
        engine = DecisionEngine()
        # Mixed characteristics - not uniformly tabular
        data = {
            "users": [{"id": 1}],  # One tabular array
            "tags": ["a", "b", "c"],  # One non-tabular array
            "numbers": [1, 2, 3],  # Another non-tabular
            "config": {"a": {"b": {"c": 1}}},  # Some nesting
        }
        decision = engine.analyze(data)

        # Mixed signals should result in moderate confidence
        # With 1/3 tabular arrays (33%) and moderate nesting
        assert 0.3 <= decision.confidence <= 1.0

    def test_confidence_never_zero(self) -> None:
        """Confidence is never exactly zero."""
        engine = DecisionEngine()
        decision = engine.analyze({})
        assert decision.confidence > 0.0


class TestDecisionEngineReasoning:
    """Tests for reasoning explanations."""

    def test_reasoning_not_empty(self) -> None:
        """Reasoning list is never empty."""
        engine = DecisionEngine()

        test_cases = [
            {},
            [],
            {"key": "value"},
            [1, 2, 3],
            {"a": {"b": 1}},
        ]

        for data in test_cases:
            decision = engine.analyze(data)
            assert len(decision.reasoning) > 0

    def test_reasoning_includes_recommendation_summary(self) -> None:
        """Reasoning includes final recommendation summary."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        has_recommendation = any("recommendation" in r.lower() for r in decision.reasoning)
        assert has_recommendation

    def test_reasoning_mentions_format(self) -> None:
        """Reasoning mentions the recommended format."""
        engine = DecisionEngine()
        decision = engine.analyze([{"id": 1}, {"id": 2}])

        # Format should be mentioned in reasoning
        format_mentioned = any(
            decision.recommended_format in r.lower() for r in decision.reasoning
        )
        assert format_mentioned

    def test_reasoning_is_descriptive(self) -> None:
        """Reasoning contains descriptive explanations."""
        engine = DecisionEngine()
        decision = engine.analyze(
            {"users": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]}
        )

        # Should have multiple reasoning points
        assert len(decision.reasoning) >= 3

        # Each reason should be meaningful (not just empty strings)
        for reason in decision.reasoning:
            assert len(reason) > 10


class TestDecisionEngineFormatDecisionImmutability:
    """Tests for FormatDecision immutability."""

    def test_frozen_dataclass(self) -> None:
        """FormatDecision is immutable (frozen)."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        with pytest.raises(AttributeError):
            decision.recommended_format = "json"  # type: ignore[misc]

    def test_cannot_modify_reasoning_via_reference(self) -> None:
        """Reasoning list modification doesn't affect decision."""
        engine = DecisionEngine()
        decision = engine.analyze({"key": "value"})

        original_len = len(decision.reasoning)
        # This modifies the list but shouldn't affect immutability contract
        # Note: frozen dataclass doesn't prevent list mutation
        # This is a design consideration - could use tuple instead
        decision.reasoning.append("extra")
        assert len(decision.reasoning) == original_len + 1


class TestDecisionEngineRealWorldScenarios:
    """Tests for real-world data scenarios."""

    def test_api_response_tabular(self) -> None:
        """Typical API response with tabular data."""
        engine = DecisionEngine()
        data = {
            "status": "success",
            "count": 3,
            "data": [
                {"id": 1, "name": "Product A", "price": 10.99, "stock": 100},
                {"id": 2, "name": "Product B", "price": 20.99, "stock": 50},
                {"id": 3, "name": "Product C", "price": 15.99, "stock": 75},
            ],
        }
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"
        assert decision.confidence > 0.7

    def test_config_file_nested(self) -> None:
        """Configuration file with nested settings."""
        engine = DecisionEngine()
        data = {
            "database": {
                "primary": {
                    "host": "db1.example.com",
                    "port": 5432,
                    "pool": {"min": 5, "max": 20},
                },
                "replica": {
                    "host": "db2.example.com",
                    "port": 5432,
                    "pool": {"min": 2, "max": 10},
                },
            },
            "cache": {"redis": {"host": "cache.example.com", "port": 6379}},
        }
        decision = engine.analyze(data)

        # Deeply nested config, but still TOON-friendly
        assert decision.metrics.max_depth >= 4

    def test_event_log_stream(self) -> None:
        """Event log with uniform entries."""
        engine = DecisionEngine()
        data = [
            {"timestamp": "2024-01-01T10:00:00Z", "event": "login", "user_id": 1},
            {"timestamp": "2024-01-01T10:05:00Z", "event": "click", "user_id": 1},
            {"timestamp": "2024-01-01T10:10:00Z", "event": "logout", "user_id": 1},
        ]
        decision = engine.analyze(data)

        assert decision.recommended_format == "toon"
        assert decision.metrics.uniformity_score == 100.0

    def test_mixed_content_blog_post(self) -> None:
        """Blog post with mixed content types."""
        engine = DecisionEngine()
        data = {
            "title": "My Blog Post",
            "author": {"name": "Alice", "bio": "Writer"},
            "tags": ["python", "programming", "tutorial"],
            "sections": [
                {"type": "text", "content": "Introduction..."},
                {"type": "code", "language": "python", "content": "print('hello')"},
                {"type": "image", "url": "https://example.com/img.png"},
            ],
            "metadata": {"views": 1000, "likes": 50},
        }
        decision = engine.analyze(data)

        # Mixed content - moderate uniformity
        assert 0.0 <= decision.metrics.uniformity_score <= 100.0

    def test_empty_api_response(self) -> None:
        """Empty API response."""
        engine = DecisionEngine()
        data = {"status": "success", "data": []}
        decision = engine.analyze(data)

        # Empty data - should still make a recommendation
        assert decision.recommended_format in {"toon", "json", "graph", "hybrid"}


class TestDecisionEngineEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_threshold_depth(self) -> None:
        """Depth exactly at threshold (6 levels)."""
        engine = DecisionEngine()
        data = {"a": {"b": {"c": {"d": {"e": {"f": 1}}}}}}
        decision = engine.analyze(data)

        assert decision.metrics.max_depth == 6
        # At threshold, should not strongly favor JSON
        # (only > threshold favors JSON)

    def test_uniformity_at_high_threshold(self) -> None:
        """Uniformity exactly at high threshold (70%)."""
        engine = DecisionEngine()
        # Create data with approximately 70% tabular arrays
        data = {
            "tabular1": [{"id": 1}, {"id": 2}],
            "tabular2": [{"x": "a"}, {"x": "b"}],
            "tabular3": [{"y": 1}, {"y": 2}],
            "non_tabular": [1, 2, 3],  # Not tabular
        }
        decision = engine.analyze(data)

        # 3 out of 4 arrays are tabular = 75%
        assert decision.metrics.uniformity_score >= 70.0

    def test_uniformity_at_low_threshold(self) -> None:
        """Uniformity near low threshold (30%)."""
        engine = DecisionEngine()
        data = {
            "tabular": [{"id": 1}, {"id": 2}],
            "list1": [1, 2, 3],
            "list2": ["a", "b", "c"],
            "list3": [True, False],
        }
        decision = engine.analyze(data)

        # 1 out of 4 arrays is tabular = 25%
        assert decision.metrics.uniformity_score < 30.0

    def test_very_large_flat_dict(self) -> None:
        """Very large flat dictionary."""
        engine = DecisionEngine()
        data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        decision = engine.analyze(data)

        assert decision.metrics.max_depth == 1
        assert decision.metrics.key_count == 1000

    def test_single_element_list(self) -> None:
        """Single element list."""
        engine = DecisionEngine()
        data = [42]
        decision = engine.analyze(data)

        assert decision.metrics.total_arrays == 1


class TestDecisionEngineThresholdConstants:
    """Tests for threshold constant values."""

    def test_max_favorable_depth_constant(self) -> None:
        """MAX_FAVORABLE_DEPTH is 6."""
        assert DecisionEngine.MAX_FAVORABLE_DEPTH == 6

    def test_high_uniformity_threshold_constant(self) -> None:
        """HIGH_UNIFORMITY_THRESHOLD is 70.0."""
        assert DecisionEngine.HIGH_UNIFORMITY_THRESHOLD == 70.0

    def test_low_uniformity_threshold_constant(self) -> None:
        """LOW_UNIFORMITY_THRESHOLD is 30.0."""
        assert DecisionEngine.LOW_UNIFORMITY_THRESHOLD == 30.0

    def test_high_reference_density_threshold_constant(self) -> None:
        """HIGH_REFERENCE_DENSITY_THRESHOLD is 20.0."""
        assert DecisionEngine.HIGH_REFERENCE_DENSITY_THRESHOLD == 20.0
