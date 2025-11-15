"""Unit tests for KeyFoldingEngine.

This module provides comprehensive tests for the KeyFoldingEngine class,
covering single-key chains, multi-key objects, special characters, nested
structures, and edge cases.
"""

from __future__ import annotations

import pytest

from pytoon.encoder.keyfolding import KeyFoldingEngine


class TestKeyFoldingEngineBasics:
    """Basic functionality tests for KeyFoldingEngine."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_empty_dict(self) -> None:
        """Empty dict should return empty dict."""
        result = self.engine.fold({})
        assert result == {}

    def test_single_key_value(self) -> None:
        """Single key-value pair with primitive value."""
        result = self.engine.fold({"key": "value"})
        assert result == {"key": "value"}

    def test_single_key_number(self) -> None:
        """Single key with numeric value."""
        result = self.engine.fold({"count": 42})
        assert result == {"count": 42}

    def test_single_key_boolean(self) -> None:
        """Single key with boolean value."""
        result = self.engine.fold({"active": True})
        assert result == {"active": True}

    def test_single_key_none(self) -> None:
        """Single key with None value."""
        result = self.engine.fold({"data": None})
        assert result == {"data": None}


class TestSingleKeyChainFolding:
    """Tests for collapsing single-key wrapper chains."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_two_level_chain(self) -> None:
        """Two-level single-key chain should fold."""
        result = self.engine.fold({"a": {"b": 1}})
        assert result == {"a.b": 1}

    def test_three_level_chain(self) -> None:
        """Three-level single-key chain should fold."""
        result = self.engine.fold({"a": {"b": {"c": 1}}})
        assert result == {"a.b.c": 1}

    def test_four_level_chain(self) -> None:
        """Four-level single-key chain should fold."""
        result = self.engine.fold({"a": {"b": {"c": {"d": "value"}}}})
        assert result == {"a.b.c.d": "value"}

    def test_deep_nesting_chain(self) -> None:
        """Deep single-key chain should fold completely."""
        data = {"level1": {"level2": {"level3": {"level4": {"level5": 100}}}}}
        result = self.engine.fold(data)
        assert result == {"level1.level2.level3.level4.level5": 100}

    def test_chain_with_string_value(self) -> None:
        """Chain terminating in string."""
        result = self.engine.fold({"config": {"database": {"host": "localhost"}}})
        assert result == {"config.database.host": "localhost"}

    def test_chain_with_boolean_value(self) -> None:
        """Chain terminating in boolean."""
        result = self.engine.fold({"settings": {"debug": {"enabled": False}}})
        assert result == {"settings.debug.enabled": False}

    def test_chain_with_float_value(self) -> None:
        """Chain terminating in float."""
        result = self.engine.fold({"metrics": {"cpu": {"usage": 75.5}}})
        assert result == {"metrics.cpu.usage": 75.5}

    def test_chain_with_none_value(self) -> None:
        """Chain terminating in None."""
        result = self.engine.fold({"data": {"result": {"value": None}}})
        assert result == {"data.result.value": None}

    def test_camelcase_keys(self) -> None:
        """CamelCase keys should fold."""
        result = self.engine.fold({"userData": {"profileInfo": {"lastName": "Smith"}}})
        assert result == {"userData.profileInfo.lastName": "Smith"}

    def test_underscore_keys(self) -> None:
        """Keys with underscores should fold."""
        result = self.engine.fold({"user_data": {"profile_info": {"last_name": "Smith"}}})
        assert result == {"user_data.profile_info.last_name": "Smith"}

    def test_numeric_suffix_keys(self) -> None:
        """Keys with numeric suffixes should fold."""
        result = self.engine.fold({"data1": {"data2": {"data3": "value"}}})
        assert result == {"data1.data2.data3": "value"}


class TestMultiKeyObjectsNoFold:
    """Tests for multi-key objects that should NOT be folded."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_multi_key_at_root(self) -> None:
        """Multiple keys at root should not trigger folding."""
        data = {"a": 1, "b": 2}
        result = self.engine.fold(data)
        assert result == {"a": 1, "b": 2}

    def test_multi_key_stops_folding(self) -> None:
        """Multi-key object should stop the folding chain."""
        data = {"a": {"b": 1, "c": 2}}
        result = self.engine.fold(data)
        assert result == {"a": {"b": 1, "c": 2}}

    def test_multi_key_nested(self) -> None:
        """Multi-key nested object should stop folding."""
        data = {"outer": {"inner": {"key1": "val1", "key2": "val2"}}}
        result = self.engine.fold(data)
        assert result == {"outer.inner": {"key1": "val1", "key2": "val2"}}

    def test_multi_key_preserves_structure(self) -> None:
        """Multi-key objects should preserve their structure."""
        data = {"config": {"server": {"host": "localhost", "port": 8080}}}
        result = self.engine.fold(data)
        assert result == {"config.server": {"host": "localhost", "port": 8080}}

    def test_complex_multi_key(self) -> None:
        """Complex multi-key object with various types."""
        data = {
            "root": {
                "config": {
                    "name": "app",
                    "version": "1.0",
                    "debug": True,
                    "count": 42,
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {
            "root.config": {
                "name": "app",
                "version": "1.0",
                "debug": True,
                "count": 42,
            }
        }


class TestNonDictValuesNoFold:
    """Tests for non-dict values that should NOT be folded."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_list_value_no_fold(self) -> None:
        """List value should stop folding."""
        result = self.engine.fold({"a": [1, 2, 3]})
        assert result == {"a": [1, 2, 3]}

    def test_empty_list_value(self) -> None:
        """Empty list value."""
        result = self.engine.fold({"items": []})
        assert result == {"items": []}

    def test_string_value_no_fold(self) -> None:
        """String value terminates chain."""
        result = self.engine.fold({"key": "value"})
        assert result == {"key": "value"}

    def test_number_value_no_fold(self) -> None:
        """Number value terminates chain."""
        result = self.engine.fold({"count": 100})
        assert result == {"count": 100}

    def test_boolean_value_no_fold(self) -> None:
        """Boolean value terminates chain."""
        result = self.engine.fold({"flag": True})
        assert result == {"flag": True}

    def test_none_value_no_fold(self) -> None:
        """None value terminates chain."""
        result = self.engine.fold({"value": None})
        assert result == {"value": None}

    def test_list_with_dicts(self) -> None:
        """List containing dicts should recursively fold those dicts."""
        data = {"items": [{"a": {"b": 1}}, {"c": {"d": 2}}]}
        result = self.engine.fold(data)
        assert result == {"items": [{"a.b": 1}, {"c.d": 2}]}

    def test_nested_list_with_dicts(self) -> None:
        """Nested lists with dicts should be recursively processed."""
        data = {"outer": {"inner": [[{"a": {"b": 1}}]]}}
        result = self.engine.fold(data)
        assert result == {"outer.inner": [[{"a.b": 1}]]}


class TestKeysWithDotsNoFold:
    """Tests for keys containing dots that should NOT be folded."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_key_with_dot_no_fold(self) -> None:
        """Key containing a dot should not be folded."""
        result = self.engine.fold({"a.b": {"c": 1}})
        # The outer key "a.b" has a dot, so _is_foldable_key returns False
        # So the chain starting from "a.b" will not fold
        # But {"c": 1} is the value, and when we recursively call fold() on it,
        # it will return {"c": 1} (single key-value, no nested dict to fold)
        assert result == {"a.b": {"c": 1}}

    def test_nested_key_with_dot(self) -> None:
        """Nested key with dot should stop folding."""
        data = {"a": {"b.c": {"d": 1}}}
        result = self.engine.fold(data)
        # "a" is safe, so we try to fold
        # "b.c" has a dot, so _is_foldable_key returns False
        # The fold chain stops, but we still recursively process {"b.c": {"d": 1}}
        assert result == {"a": {"b.c": {"d": 1}}}

    def test_multiple_dots_in_key(self) -> None:
        """Key with multiple dots."""
        result = self.engine.fold({"a.b.c": 1})
        assert result == {"a.b.c": 1}

    def test_dot_at_start(self) -> None:
        """Key starting with dot."""
        result = self.engine.fold({".hidden": 1})
        assert result == {".hidden": 1}

    def test_dot_at_end(self) -> None:
        """Key ending with dot."""
        result = self.engine.fold({"key.": 1})
        assert result == {"key.": 1}


class TestSpecialCharactersNoFold:
    """Tests for keys with special characters that should NOT be folded."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_dash_in_key(self) -> None:
        """Key with dash should not fold."""
        result = self.engine.fold({"key-name": {"sub": 1}})
        assert result == {"key-name": {"sub": 1}}

    def test_space_in_key(self) -> None:
        """Key with space should not fold."""
        result = self.engine.fold({"key name": {"sub": 1}})
        assert result == {"key name": {"sub": 1}}

    def test_leading_underscore(self) -> None:
        """Key starting with underscore should not fold (private key protection)."""
        result = self.engine.fold({"_private": {"data": 1}})
        assert result == {"_private": {"data": 1}}

    def test_special_chars(self) -> None:
        """Keys with various special characters."""
        test_cases = [
            ({"key@name": {"sub": 1}}, {"key@name": {"sub": 1}}),
            ({"key#name": {"sub": 1}}, {"key#name": {"sub": 1}}),
            ({"key$name": {"sub": 1}}, {"key$name": {"sub": 1}}),
            ({"key%name": {"sub": 1}}, {"key%name": {"sub": 1}}),
            ({"key!name": {"sub": 1}}, {"key!name": {"sub": 1}}),
        ]
        for data, expected in test_cases:
            result = self.engine.fold(data)
            assert result == expected

    def test_numeric_start(self) -> None:
        """Key starting with number should not fold."""
        result = self.engine.fold({"123key": {"sub": 1}})
        assert result == {"123key": {"sub": 1}}

    def test_empty_key(self) -> None:
        """Empty key should not fold."""
        result = self.engine.fold({"": {"sub": 1}})
        assert result == {"": {"sub": 1}}


class TestMixedStructures:
    """Tests for mixed structures with both foldable and non-foldable parts."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_mixed_foldable_and_non_foldable(self) -> None:
        """Mix of foldable and non-foldable keys."""
        data = {
            "a": {"b": {"c": 1}},  # Foldable
            "x": {"y": 2, "z": 3},  # Multi-key, stops folding
        }
        result = self.engine.fold(data)
        assert result == {"a.b.c": 1, "x": {"y": 2, "z": 3}}

    def test_partial_folding(self) -> None:
        """Partial folding with multi-key stopping the chain."""
        data = {
            "level1": {
                "level2": {
                    "data": {
                        "key1": "val1",
                        "key2": "val2",
                    }
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {"level1.level2.data": {"key1": "val1", "key2": "val2"}}

    def test_complex_nested_structure(self) -> None:
        """Complex structure with various nesting patterns."""
        data = {
            "config": {
                "database": {
                    "primary": {
                        "host": "localhost",
                        "port": 5432,
                    },
                    "secondary": {
                        "host": "backup.local",
                        "port": 5433,
                    },
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {
            "config.database": {
                "primary": {"host": "localhost", "port": 5432},
                "secondary": {"host": "backup.local", "port": 5433},
            }
        }

    def test_arrays_within_folded_structure(self) -> None:
        """Arrays within folded structures."""
        data = {"data": {"results": {"items": [1, 2, 3]}}}
        result = self.engine.fold(data)
        assert result == {"data.results.items": [1, 2, 3]}

    def test_recursive_folding_in_multi_key(self) -> None:
        """Multi-key objects should still have their values recursively folded."""
        data = {
            "a": {
                "b": {"c": {"d": 1}},  # This should fold to c.d
                "e": {"f": {"g": 2}},  # This should fold to f.g
            }
        }
        result = self.engine.fold(data)
        assert result == {"a": {"b.c.d": 1, "e.f.g": 2}}


class TestEmptyAndEdgeCases:
    """Tests for empty dicts and edge cases."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_empty_nested_dict(self) -> None:
        """Single key with empty dict value."""
        result = self.engine.fold({"a": {}})
        assert result == {"a": {}}

    def test_deeply_nested_empty_dict(self) -> None:
        """Chain leading to empty dict."""
        result = self.engine.fold({"a": {"b": {"c": {}}}})
        # Empty dict doesn't continue folding, so we get "a.b.c" with value {}
        assert result == {"a.b.c": {}}

    def test_multiple_empty_dicts(self) -> None:
        """Multiple keys with empty dict values."""
        result = self.engine.fold({"a": {}, "b": {}})
        assert result == {"a": {}, "b": {}}

    def test_single_key_single_letter(self) -> None:
        """Single letter keys should fold."""
        result = self.engine.fold({"a": {"b": {"c": "x"}}})
        assert result == {"a.b.c": "x"}

    def test_very_long_key_names(self) -> None:
        """Very long key names should still fold if valid."""
        long_key = "a" * 100
        result = self.engine.fold({long_key: {"sub": 1}})
        assert result == {f"{long_key}.sub": 1}

    def test_preserves_value_types(self) -> None:
        """Various value types should be preserved."""
        data = {
            "str": {"value": "text"},
            "int": {"value": 42},
            "float": {"value": 3.14},
            "bool": {"value": True},
            "none": {"value": None},
            "list": {"value": [1, 2, 3]},
        }
        result = self.engine.fold(data)
        assert result == {
            "str.value": "text",
            "int.value": 42,
            "float.value": 3.14,
            "bool.value": True,
            "none.value": None,
            "list.value": [1, 2, 3],
        }


class TestIsFoldableKey:
    """Tests for _is_foldable_key method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_simple_identifier(self) -> None:
        """Simple identifier should be foldable."""
        assert self.engine._is_foldable_key("name") is True

    def test_camelcase(self) -> None:
        """CamelCase identifier should be foldable."""
        assert self.engine._is_foldable_key("userName") is True

    def test_underscore_middle(self) -> None:
        """Underscore in middle should be foldable."""
        assert self.engine._is_foldable_key("user_name") is True

    def test_with_numbers(self) -> None:
        """Numbers in identifier should be foldable."""
        assert self.engine._is_foldable_key("data123") is True

    def test_leading_underscore_not_foldable(self) -> None:
        """Leading underscore should not be foldable."""
        assert self.engine._is_foldable_key("_private") is False

    def test_dot_not_foldable(self) -> None:
        """Dot in key should not be foldable."""
        assert self.engine._is_foldable_key("a.b") is False

    def test_dash_not_foldable(self) -> None:
        """Dash in key should not be foldable."""
        assert self.engine._is_foldable_key("key-name") is False

    def test_space_not_foldable(self) -> None:
        """Space in key should not be foldable."""
        assert self.engine._is_foldable_key("key name") is False

    def test_empty_string_not_foldable(self) -> None:
        """Empty string should not be foldable."""
        assert self.engine._is_foldable_key("") is False

    def test_number_start_not_foldable(self) -> None:
        """Key starting with number should not be foldable."""
        assert self.engine._is_foldable_key("123key") is False


class TestCanFoldPath:
    """Tests for _can_fold_path method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_single_key_dict(self) -> None:
        """Single key dict should be foldable."""
        assert self.engine._can_fold_path({"a": 1}) is True

    def test_single_key_nested_dict(self) -> None:
        """Single key nested dict should be foldable."""
        assert self.engine._can_fold_path({"a": {"b": 1}}) is True

    def test_multi_key_dict(self) -> None:
        """Multi-key dict should not be foldable."""
        assert self.engine._can_fold_path({"a": 1, "b": 2}) is False

    def test_empty_dict(self) -> None:
        """Empty dict should not be foldable."""
        assert self.engine._can_fold_path({}) is False

    def test_list(self) -> None:
        """List should not be foldable."""
        assert self.engine._can_fold_path([1, 2]) is False

    def test_string(self) -> None:
        """String should not be foldable."""
        assert self.engine._can_fold_path("string") is False

    def test_number(self) -> None:
        """Number should not be foldable."""
        assert self.engine._can_fold_path(42) is False

    def test_none(self) -> None:
        """None should not be foldable."""
        assert self.engine._can_fold_path(None) is False

    def test_single_key_with_dot(self) -> None:
        """Single key with dot should not be foldable."""
        assert self.engine._can_fold_path({"a.b": 1}) is False

    def test_single_key_with_special_char(self) -> None:
        """Single key with special char should not be foldable."""
        assert self.engine._can_fold_path({"key-name": 1}) is False


class TestRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = KeyFoldingEngine()

    def test_api_response_structure(self) -> None:
        """API response with nested data."""
        data = {
            "response": {
                "data": {
                    "user": {
                        "id": 123,
                        "name": "Alice",
                        "email": "alice@example.com",
                    }
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {
            "response.data.user": {
                "id": 123,
                "name": "Alice",
                "email": "alice@example.com",
            }
        }

    def test_config_file_structure(self) -> None:
        """Configuration file with deep nesting."""
        data = {
            "app": {
                "settings": {
                    "logging": {"level": "INFO", "format": "json", "output": "stdout"}
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {
            "app.settings.logging": {
                "level": "INFO",
                "format": "json",
                "output": "stdout",
            }
        }

    def test_metadata_wrapper(self) -> None:
        """Metadata wrapper pattern."""
        data = {
            "meta": {"timestamp": "2025-11-16T00:00:00Z"},
            "data": {"items": [{"id": 1}, {"id": 2}]},
        }
        result = self.engine.fold(data)
        assert result == {
            "meta.timestamp": "2025-11-16T00:00:00Z",
            "data.items": [{"id": 1}, {"id": 2}],
        }

    def test_error_response(self) -> None:
        """Error response structure."""
        data = {
            "error": {
                "details": {
                    "code": "AUTH_FAILED",
                    "message": "Invalid credentials",
                    "retry": False,
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {
            "error.details": {
                "code": "AUTH_FAILED",
                "message": "Invalid credentials",
                "retry": False,
            }
        }

    def test_deeply_nested_single_value(self) -> None:
        """Deeply nested single value pattern."""
        data = {
            "root": {
                "child": {
                    "grandchild": {
                        "value": "deeply nested"
                    }
                }
            }
        }
        result = self.engine.fold(data)
        assert result == {"root.child.grandchild.value": "deeply nested"}
