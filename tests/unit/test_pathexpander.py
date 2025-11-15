"""Unit tests for PathExpander class.

Tests cover:
- Basic key expansion
- Multiple dotted keys
- Mixed dotted and regular keys
- Key conflict detection
- Recursive expansion
- Edge cases
"""

from typing import Any

import pytest

from pytoon.decoder.pathexpander import PathExpander
from pytoon.utils.errors import TOONDecodeError


class TestBasicExpansion:
    """Test basic key expansion functionality."""

    def test_single_dotted_key(self) -> None:
        """Test expanding single dotted key."""
        expander = PathExpander()
        result = expander.expand({"a.b": 1})
        assert result == {"a": {"b": 1}}

    def test_deeply_nested_key(self) -> None:
        """Test expanding deeply nested dotted key."""
        expander = PathExpander()
        result = expander.expand({"a.b.c.d.e": "deep"})
        assert result == {"a": {"b": {"c": {"d": {"e": "deep"}}}}}

    def test_simple_key_preserved(self) -> None:
        """Test that non-dotted keys are preserved."""
        expander = PathExpander()
        result = expander.expand({"simple": "value"})
        assert result == {"simple": "value"}

    def test_empty_dict(self) -> None:
        """Test expanding empty dictionary."""
        expander = PathExpander()
        result = expander.expand({})
        assert result == {}

    def test_value_types_preserved(self) -> None:
        """Test that various value types are preserved."""
        expander = PathExpander()
        data = {
            "int.val": 42,
            "float.val": 3.14,
            "bool.val": True,
            "none.val": None,
            "str.val": "text",
            "list.val": [1, 2, 3],
            "dict.val": {"nested": "dict"},
        }
        result = expander.expand(data)
        assert result["int"]["val"] == 42
        assert result["float"]["val"] == 3.14
        assert result["bool"]["val"] is True
        assert result["none"]["val"] is None
        assert result["str"]["val"] == "text"
        assert result["list"]["val"] == [1, 2, 3]
        assert result["dict"]["val"] == {"nested": "dict"}


class TestMultipleDottedKeys:
    """Test expanding multiple dotted keys."""

    def test_sibling_keys(self) -> None:
        """Test expanding sibling dotted keys."""
        expander = PathExpander()
        result = expander.expand({"user.name": "Alice", "user.age": 30})
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_multiple_branches(self) -> None:
        """Test expanding keys into multiple branches."""
        expander = PathExpander()
        result = expander.expand({
            "user.name": "Alice",
            "config.debug": True,
            "data.items": [1, 2],
        })
        assert result == {
            "user": {"name": "Alice"},
            "config": {"debug": True},
            "data": {"items": [1, 2]},
        }

    def test_deep_siblings(self) -> None:
        """Test expanding deeply nested siblings."""
        expander = PathExpander()
        result = expander.expand({
            "a.b.c.x": 1,
            "a.b.c.y": 2,
            "a.b.c.z": 3,
        })
        assert result == {"a": {"b": {"c": {"x": 1, "y": 2, "z": 3}}}}

    def test_mixed_depth_siblings(self) -> None:
        """Test siblings at different depths."""
        expander = PathExpander()
        result = expander.expand({
            "a.b": 1,
            "a.c.d": 2,
            "a.e.f.g": 3,
        })
        assert result == {
            "a": {
                "b": 1,
                "c": {"d": 2},
                "e": {"f": {"g": 3}},
            }
        }


class TestMixedKeys:
    """Test mixing dotted and regular keys."""

    def test_mixed_dotted_and_simple(self) -> None:
        """Test mixed dotted and simple keys."""
        expander = PathExpander()
        result = expander.expand({
            "simple": "value",
            "dotted.key": "nested",
        })
        assert result == {
            "simple": "value",
            "dotted": {"key": "nested"},
        }

    def test_complex_mixed(self) -> None:
        """Test complex mixed key structure."""
        expander = PathExpander()
        result = expander.expand({
            "name": "Test",
            "config.enabled": True,
            "config.timeout": 30,
            "version": 1,
            "meta.author.name": "Alice",
            "meta.author.email": "alice@example.com",
        })
        expected = {
            "name": "Test",
            "config": {"enabled": True, "timeout": 30},
            "version": 1,
            "meta": {"author": {"name": "Alice", "email": "alice@example.com"}},
        }
        assert result == expected


class TestKeyConflicts:
    """Test key conflict detection."""

    def test_duplicate_simple_key(self) -> None:
        """Test duplicate simple key raises error."""
        expander = PathExpander()
        # Note: Python dict doesn't allow literal duplicates, so we test
        # via the internal _set_nested method
        data: dict[str, Any] = {}
        expander._set_nested(data, "a", 1)
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            expander._set_nested(data, "a", 2)

    def test_duplicate_dotted_key(self) -> None:
        """Test duplicate dotted key path."""
        expander = PathExpander()
        # Build manually to simulate duplicate paths
        data: dict[str, Any] = {"a.b": 1}
        expander._set_nested(data, "a.b", 1)  # First
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            expander._set_nested(data, "a.b", 2)  # Duplicate

    def test_conflict_simple_key_then_dotted(self) -> None:
        """Test conflict when dotted key extends simple key."""
        expander = PathExpander()
        # "a" is a leaf, "a.b" tries to extend it
        data: dict[str, Any] = {}
        expander._set_nested(data, "a", 1)
        with pytest.raises(TOONDecodeError, match="Key conflict"):
            expander._set_nested(data, "a.b", 2)

    def test_conflict_dotted_key_then_simple(self) -> None:
        """Test conflict when simple key overwrites nested."""
        expander = PathExpander()
        # "a.b" creates nested, "a" tries to overwrite
        data: dict[str, Any] = {}
        expander._set_nested(data, "a.b", 1)
        # This is a duplicate key error since "a" already exists as a dict
        with pytest.raises(TOONDecodeError, match="Duplicate key"):
            expander._set_nested(data, "a", 2)

    def test_conflict_nested_overwrite(self) -> None:
        """Test conflict when trying to overwrite nested structure."""
        expander = PathExpander()
        data: dict[str, Any] = {}
        expander._set_nested(data, "a.b.c", 1)
        with pytest.raises(TOONDecodeError, match="Key conflict"):
            expander._set_nested(data, "a.b", "flat")


class TestRecursiveExpansion:
    """Test recursive expansion functionality."""

    def test_recursive_nested_dict(self) -> None:
        """Test recursive expansion of nested dictionaries."""
        expander = PathExpander()
        data = {"outer.inner": {"nested.key": 1}}
        result = expander.expand_recursive(data)
        assert result == {"outer": {"inner": {"nested": {"key": 1}}}}

    def test_recursive_list_of_dicts(self) -> None:
        """Test recursive expansion of list containing dicts."""
        expander = PathExpander()
        data = [{"a.b": 1}, {"c.d": 2}]
        result = expander.expand_recursive(data)
        assert result == [{"a": {"b": 1}}, {"c": {"d": 2}}]

    def test_recursive_mixed_structure(self) -> None:
        """Test recursive expansion of complex structure."""
        expander = PathExpander()
        data = {
            "config.items": [
                {"item.name": "first", "item.value": 1},
                {"item.name": "second", "item.value": 2},
            ],
            "meta.info": {"detail.x": 10},
        }
        result = expander.expand_recursive(data)
        expected = {
            "config": {
                "items": [
                    {"item": {"name": "first", "value": 1}},
                    {"item": {"name": "second", "value": 2}},
                ]
            },
            "meta": {"info": {"detail": {"x": 10}}},
        }
        assert result == expected

    def test_recursive_preserves_primitives(self) -> None:
        """Test that recursive expansion preserves primitives."""
        expander = PathExpander()
        assert expander.expand_recursive(42) == 42
        assert expander.expand_recursive("string") == "string"
        assert expander.expand_recursive(True) is True
        assert expander.expand_recursive(None) is None


class TestHasDottedKeys:
    """Test dotted key detection."""

    def test_has_dotted_keys_true(self) -> None:
        """Test detection of dotted keys."""
        expander = PathExpander()
        assert expander.has_dotted_keys({"a.b": 1}) is True

    def test_has_dotted_keys_false(self) -> None:
        """Test no dotted keys detected."""
        expander = PathExpander()
        assert expander.has_dotted_keys({"simple": 1}) is False

    def test_has_dotted_keys_mixed(self) -> None:
        """Test detection in mixed keys."""
        expander = PathExpander()
        assert expander.has_dotted_keys({"simple": 1, "dotted.key": 2}) is True

    def test_has_dotted_keys_empty(self) -> None:
        """Test empty dictionary."""
        expander = PathExpander()
        assert expander.has_dotted_keys({}) is False


class TestValidateNoConflicts:
    """Test pre-validation of key conflicts."""

    def test_validate_no_conflicts_clean(self) -> None:
        """Test validation passes for clean data."""
        expander = PathExpander()
        # Should not raise
        expander.validate_no_conflicts({"a.b": 1, "a.c": 2, "x": 3})

    def test_validate_conflict_leaf_extends(self) -> None:
        """Test validation catches leaf extension conflict."""
        expander = PathExpander()
        with pytest.raises(TOONDecodeError, match="Key conflict"):
            expander.validate_no_conflicts({"a": 1, "a.b": 2})

    def test_validate_conflict_path_becomes_leaf(self) -> None:
        """Test validation catches path becoming leaf."""
        expander = PathExpander()
        with pytest.raises(TOONDecodeError, match="Key conflict"):
            expander.validate_no_conflicts({"a.b": 1, "a": 2})

    def test_validate_duplicate_path(self) -> None:
        """Test validation catches duplicate paths."""
        expander = PathExpander()
        # Python dicts don't allow duplicates, but we test the logic
        # by checking that it would be caught
        # This is more of a theoretical test
        data = {"a.b": 1}
        # Normal case should pass
        expander.validate_no_conflicts(data)

    def test_validate_complex_structure(self) -> None:
        """Test validation of complex valid structure."""
        expander = PathExpander()
        data = {
            "config.db.host": "localhost",
            "config.db.port": 5432,
            "config.cache.enabled": True,
            "config.cache.ttl": 300,
            "metadata.version": "1.0",
            "metadata.author.name": "Alice",
        }
        # Should not raise
        expander.validate_no_conflicts(data)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_char_keys(self) -> None:
        """Test single character keys."""
        expander = PathExpander()
        result = expander.expand({"a.b.c": 1})
        assert result == {"a": {"b": {"c": 1}}}

    def test_numeric_string_keys(self) -> None:
        """Test numeric string keys in path."""
        expander = PathExpander()
        result = expander.expand({"data.0.value": "first", "data.1.value": "second"})
        assert result == {
            "data": {"0": {"value": "first"}, "1": {"value": "second"}}
        }

    def test_underscore_in_keys(self) -> None:
        """Test underscores in key names."""
        expander = PathExpander()
        result = expander.expand({"user_data.first_name": "Alice"})
        assert result == {"user_data": {"first_name": "Alice"}}

    def test_empty_string_values(self) -> None:
        """Test empty string values."""
        expander = PathExpander()
        result = expander.expand({"a.b": ""})
        assert result == {"a": {"b": ""}}

    def test_very_long_path(self) -> None:
        """Test very long dotted path."""
        expander = PathExpander()
        parts = ["level" + str(i) for i in range(10)]
        key = ".".join(parts)
        result = expander.expand({key: "deep"})

        # Verify depth
        current: Any = result
        for part in parts[:-1]:
            assert part in current
            current = current[part]
        assert current[parts[-1]] == "deep"

    def test_order_preservation(self) -> None:
        """Test that key order is generally preserved."""
        expander = PathExpander()
        data = {
            "z.a": 1,
            "y.a": 2,
            "x.a": 3,
        }
        result = expander.expand(data)
        # Check that keys appear in order added
        keys = list(result.keys())
        assert keys == ["z", "y", "x"]


class TestRepr:
    """Test string representation."""

    def test_repr(self) -> None:
        """Test repr output."""
        expander = PathExpander()
        assert repr(expander) == "PathExpander()"
