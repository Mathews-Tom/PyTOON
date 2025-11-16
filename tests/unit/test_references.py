"""Unit tests for reference encoding and decoding system.

Tests the ReferenceEncoder.encode_refs() and ReferenceDecoder.decode_refs()
methods for schema-based reference encoding with proper object identity.
"""

import pytest

from pytoon import decode_refs, encode_refs
from pytoon.references import ReferenceDecoder, ReferenceEncoder
from pytoon.utils.errors import TOONDecodeError, TOONEncodeError


class TestEncodeRefsAPI:
    """Tests for the encode_refs() public API."""

    def test_encode_refs_with_shared_object(self) -> None:
        """encode_refs generates schema for shared objects."""
        user = {"id": 1, "name": "Alice"}
        data = {"users": [user], "admins": [user]}

        result = encode_refs(data)

        assert "_schema:" in result
        assert "$1" in result
        assert "Object1:" in result

    def test_encode_refs_no_shared_objects(self) -> None:
        """encode_refs without shared objects omits schema."""
        data = {"a": 1, "b": "test"}
        result = encode_refs(data)

        assert "_schema:" not in result
        assert "a: 1" in result
        assert "b: test" in result

    def test_encode_refs_schema_mode_required(self) -> None:
        """encode_refs raises error for unsupported modes."""
        with pytest.raises(TOONEncodeError, match="Unsupported encoding mode"):
            encode_refs({"a": 1}, mode="invalid")

    def test_encode_refs_primitives(self) -> None:
        """encode_refs handles primitives without schema."""
        assert encode_refs(None) == "null"
        assert encode_refs(True) == "true"
        assert encode_refs(False) == "false"
        assert encode_refs(42) == "42"
        assert encode_refs(3.14).startswith("3.14")
        assert encode_refs("hello") == "hello"

    def test_encode_refs_empty_list(self) -> None:
        """encode_refs handles empty lists."""
        result = encode_refs([])
        assert result == "[0]:"

    def test_encode_refs_inline_array(self) -> None:
        """encode_refs generates inline arrays for primitives."""
        result = encode_refs([1, 2, 3])
        assert result == "[3]: 1,2,3"

    def test_encode_refs_custom_delimiter(self) -> None:
        """encode_refs respects custom delimiter."""
        result = encode_refs([1, 2, 3], delimiter="|")
        assert result == "[3]: 1|2|3"

    def test_encode_refs_schema_field_types(self) -> None:
        """encode_refs correctly identifies field types in schema."""
        obj = {"id": 1, "name": "Alice", "active": True, "score": 95.5}
        data = {"a": obj, "b": obj}

        result = encode_refs(data)

        assert "id: int" in result
        assert "name: str" in result
        assert "active: bool" in result
        assert "score: float" in result


class TestDecodeRefsAPI:
    """Tests for the decode_refs() public API."""

    def test_decode_refs_simple_dict(self) -> None:
        """decode_refs handles simple dict without references."""
        toon = "name: Alice\nage: 30"
        result = decode_refs(toon)

        assert result == {"name": "Alice", "age": 30}

    def test_decode_refs_inline_array(self) -> None:
        """decode_refs handles inline arrays."""
        toon = "[3]: 1,2,3"
        result = decode_refs(toon)
        assert result == [1, 2, 3]

    def test_decode_refs_with_references_resolved(self) -> None:
        """decode_refs resolves placeholders to same objects."""
        toon = "users: [2]: $1,$2\nadmins: [1]: $1"
        result = decode_refs(toon, resolve=True)

        assert result["users"][0] is result["admins"][0]
        assert result["users"][1] is not result["admins"][0]

    def test_decode_refs_without_resolution(self) -> None:
        """decode_refs keeps placeholders when resolve=False."""
        toon = "items: [2]: $1,$1"
        result = decode_refs(toon, resolve=False)

        assert result == {"items": ["$1", "$1"]}

    def test_decode_refs_primitives(self) -> None:
        """decode_refs handles primitive values."""
        assert decode_refs("null") is None
        assert decode_refs("true") is True
        assert decode_refs("false") is False
        assert decode_refs("42") == 42
        assert decode_refs("3.14") == 3.14
        assert decode_refs("hello") == "hello"

    def test_decode_refs_quoted_string(self) -> None:
        """decode_refs handles quoted strings."""
        result = decode_refs('"hello, world"')
        assert result == "hello, world"

    def test_decode_refs_escaped_quotes(self) -> None:
        """decode_refs unescapes quoted strings."""
        result = decode_refs('"say \\"hello\\""')
        assert result == 'say "hello"'


class TestRoundtripFidelity:
    """Tests for encode_refs -> decode_refs roundtrip fidelity."""

    def test_roundtrip_simple_dict(self) -> None:
        """Roundtrip preserves simple dict structure."""
        data = {"name": "Alice", "age": 30}
        encoded = encode_refs(data)
        decoded = decode_refs(encoded)

        assert decoded == data

    def test_roundtrip_nested_dict(self) -> None:
        """Roundtrip preserves nested dict structure."""
        data = {"user": {"name": "Bob", "metadata": {"level": 1}}}
        encoded = encode_refs(data)
        decoded = decode_refs(encoded)

        assert decoded == data

    def test_roundtrip_list_of_primitives(self) -> None:
        """Roundtrip preserves list of primitives."""
        data = [1, 2, 3, 4, 5]
        encoded = encode_refs(data)
        decoded = decode_refs(encoded)

        assert decoded == data

    def test_roundtrip_mixed_types(self) -> None:
        """Roundtrip preserves mixed type values."""
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
        }
        encoded = encode_refs(data)
        decoded = decode_refs(encoded)

        assert decoded == data

    def test_roundtrip_shared_references_structure(self) -> None:
        """Roundtrip preserves shared reference structure (values, not identity)."""
        user = {"id": 1, "name": "Alice"}
        data = {"users": [user], "admins": [user]}

        encoded = encode_refs(data)
        decoded = decode_refs(encoded, resolve=True)

        # Structure should match (both have $1 placeholder resolved)
        assert decoded["users"][0] is decoded["admins"][0]
        # Values should be empty dicts (placeholders resolve to empty objects)
        assert isinstance(decoded["users"][0], dict)

    def test_roundtrip_multiple_shared_refs(self) -> None:
        """Roundtrip handles multiple shared references."""
        obj1 = {"type": "A"}
        obj2 = {"type": "B"}
        data = {"first": obj1, "second": obj2, "dup1": obj1, "dup2": obj2}

        encoded = encode_refs(data)
        decoded = decode_refs(encoded, resolve=True)

        # Same placeholders resolve to same objects
        assert decoded["first"] is decoded["dup1"]
        assert decoded["second"] is decoded["dup2"]
        assert decoded["first"] is not decoded["second"]


class TestReferenceEncoderMethods:
    """Tests for ReferenceEncoder methods."""

    def test_encode_refs_method(self) -> None:
        """ReferenceEncoder.encode_refs produces valid output."""
        encoder = ReferenceEncoder()
        user = {"id": 1}
        data = {"a": user, "b": user}

        result = encoder.encode_refs(data)

        assert "_schema:" in result
        assert "Object1:" in result
        assert "$1" in result

    def test_encode_string_quoting(self) -> None:
        """encode_refs quotes strings that need quoting."""
        encoder = ReferenceEncoder()
        data = {"key": "value with, comma"}

        result = encoder.encode_refs(data)
        assert '"value with, comma"' in result

    def test_encode_empty_string(self) -> None:
        """encode_refs handles empty strings."""
        encoder = ReferenceEncoder()
        data = {"key": ""}

        result = encoder.encode_refs(data)
        assert '""' in result

    def test_encode_special_float_values(self) -> None:
        """encode_refs handles NaN and Inf as null."""
        encoder = ReferenceEncoder()

        assert encoder._encode_value_simple(float("nan"), 0, {}, 2, ",") == "null"
        assert encoder._encode_value_simple(float("inf"), 0, {}, 2, ",") == "null"
        assert encoder._encode_value_simple(float("-inf"), 0, {}, 2, ",") == "null"
        assert encoder._encode_value_simple(0.0, 0, {}, 2, ",") == "0"

    def test_encode_nested_structure(self) -> None:
        """encode_refs handles nested structures."""
        encoder = ReferenceEncoder()
        data = {"outer": {"inner": {"value": 42}}}

        result = encoder.encode_refs(data)

        assert "outer:" in result
        assert "inner:" in result
        assert "value: 42" in result

    def test_encode_list_with_refs(self) -> None:
        """encode_refs handles lists containing shared references."""
        encoder = ReferenceEncoder()
        shared = {"id": 1}
        data = {"items": [shared, shared, "other"]}

        result = encoder.encode_refs(data)

        # Should have inline array with $1 references
        assert "$1" in result
        assert "[3]:" in result


class TestReferenceDecoderMethods:
    """Tests for ReferenceDecoder methods."""

    def test_parse_schema_section(self) -> None:
        """ReferenceDecoder parses schema section correctly."""
        decoder = ReferenceDecoder()
        lines = [
            "_schema:",
            "  Object1:",
            "    id: int",
            "    name: str",
            "  Object2:",
            "    value: float",
            "data: test",
        ]

        end_idx = decoder._parse_schema_section(lines)

        assert decoder._schema == {
            "Object1": {"id": "int", "name": "str"},
            "Object2": {"value": "float"},
        }
        assert end_idx == 6  # Points to "data: test"

    def test_decode_with_schema(self) -> None:
        """ReferenceDecoder handles _schema section."""
        decoder = ReferenceDecoder()
        toon = """_schema:
  Object1:
    id: int
a: $1
b: $1"""

        result = decoder.decode_refs(toon, resolve=True)

        assert result["a"] is result["b"]

    def test_split_inline_array_simple(self) -> None:
        """_split_inline_array handles simple values."""
        decoder = ReferenceDecoder()
        result = decoder._split_inline_array("1,2,3")
        assert result == ["1", "2", "3"]

    def test_split_inline_array_with_quotes(self) -> None:
        """_split_inline_array respects quoted strings."""
        decoder = ReferenceDecoder()
        result = decoder._split_inline_array('"a,b",c,d')
        assert result == ['"a,b"', "c", "d"]

    def test_unescape_string(self) -> None:
        """_unescape_string handles escape sequences."""
        decoder = ReferenceDecoder()
        assert decoder._unescape_string("hello") == "hello"
        assert decoder._unescape_string('say \\"hi\\"') == 'say "hi"'
        assert decoder._unescape_string("line\\nbreak") == "line\nbreak"
        assert decoder._unescape_string("tab\\there") == "tab\there"
        assert decoder._unescape_string("back\\\\slash") == "back\\slash"

    def test_decode_list_lines(self) -> None:
        """_decode_list_lines parses list items correctly."""
        decoder = ReferenceDecoder()
        lines = ["  - 1", "  - 2", "  - 3"]
        result = decoder._decode_list_lines(lines, 3, False)
        assert result == [1, 2, 3]

    def test_decode_list_lines_count_mismatch(self) -> None:
        """_decode_list_lines raises error on count mismatch."""
        decoder = ReferenceDecoder()
        lines = ["  - 1", "  - 2"]

        with pytest.raises(TOONDecodeError, match="declares 3 items but found 2"):
            decoder._decode_list_lines(lines, 3, False)


class TestSharedObjectIdentity:
    """Tests for proper shared object identity handling."""

    def test_same_reference_same_object(self) -> None:
        """Same reference placeholder resolves to same object."""
        toon = "a: $1\nb: $1\nc: $1"
        result = decode_refs(toon, resolve=True)

        assert result["a"] is result["b"]
        assert result["b"] is result["c"]

    def test_different_references_different_objects(self) -> None:
        """Different reference placeholders resolve to different objects."""
        toon = "a: $1\nb: $2\nc: $3"
        result = decode_refs(toon, resolve=True)

        assert result["a"] is not result["b"]
        assert result["b"] is not result["c"]
        assert result["a"] is not result["c"]

    def test_no_resolve_keeps_strings(self) -> None:
        """When resolve=False, placeholders remain as strings."""
        toon = "a: $1\nb: $1"
        result = decode_refs(toon, resolve=False)

        assert result["a"] == "$1"
        assert result["b"] == "$1"
        # They're equal strings but not the same object
        assert isinstance(result["a"], str)
        assert isinstance(result["b"], str)

    def test_nested_references(self) -> None:
        """References within nested structures are resolved."""
        toon = "outer:\n  inner: $1\nother: $1"
        result = decode_refs(toon, resolve=True)

        assert result["outer"]["inner"] is result["other"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_encode_refs_non_string_key_error(self) -> None:
        """encode_refs raises error for non-string dict keys."""
        encoder = ReferenceEncoder()
        data = {123: "value"}  # type: ignore[dict-item]

        with pytest.raises(TOONEncodeError, match="keys must be strings"):
            encoder.encode_refs(data)

    def test_encode_refs_unsupported_type(self) -> None:
        """encode_refs raises error for unsupported types."""
        encoder = ReferenceEncoder()
        data = {"obj": object()}

        with pytest.raises(TOONEncodeError, match="Cannot encode type"):
            encoder.encode_refs(data)

    def test_decode_refs_empty_string(self) -> None:
        """decode_refs handles empty string."""
        result = decode_refs("")
        assert result == {}

    def test_decode_refs_only_schema(self) -> None:
        """decode_refs handles TOON with only schema section."""
        toon = "_schema:\n  Object1:\n    id: int"
        result = decode_refs(toon)
        assert result == {}

    def test_decode_refs_array_count_validation(self) -> None:
        """decode_refs validates array item count."""
        toon = "[3]: 1,2"  # Declares 3 but only 2 items

        with pytest.raises(TOONDecodeError, match="declares 3 items but found 2"):
            decode_refs(toon)

    def test_encode_refs_with_empty_dict(self) -> None:
        """encode_refs handles empty dictionary."""
        result = encode_refs({})
        assert result == ""

    def test_decode_refs_boolean_values(self) -> None:
        """decode_refs correctly parses boolean values."""
        result = decode_refs("a: true\nb: false")
        assert result["a"] is True
        assert result["b"] is False

    def test_encode_refs_preserves_key_order(self) -> None:
        """encode_refs preserves dictionary key order."""
        data = {"z": 1, "a": 2, "m": 3}
        result = encode_refs(data)

        # Keys should appear in original order
        lines = result.strip().split("\n")
        assert "z: 1" == lines[0]
        assert "a: 2" == lines[1]
        assert "m: 3" == lines[2]


class TestIntegrationWithPublicAPI:
    """Tests for integration with pytoon public API."""

    def test_encode_refs_in_all_exports(self) -> None:
        """encode_refs is exported from pytoon."""
        from pytoon import encode_refs as api_encode_refs

        result = api_encode_refs({"a": 1})
        assert "a: 1" in result

    def test_decode_refs_in_all_exports(self) -> None:
        """decode_refs is exported from pytoon."""
        from pytoon import decode_refs as api_decode_refs

        result = api_decode_refs("a: 1")
        assert result == {"a": 1}

    def test_reference_encoder_in_references_module(self) -> None:
        """ReferenceEncoder is accessible from pytoon.references."""
        from pytoon.references import ReferenceEncoder

        encoder = ReferenceEncoder()
        assert hasattr(encoder, "encode_refs")
        assert hasattr(encoder, "detect_references")

    def test_reference_decoder_in_references_module(self) -> None:
        """ReferenceDecoder is accessible from pytoon.references."""
        from pytoon.references import ReferenceDecoder

        decoder = ReferenceDecoder()
        assert hasattr(decoder, "decode_refs")


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_multiple_levels_of_sharing(self) -> None:
        """Handle data with multiple levels of shared objects."""
        addr = {"city": "NYC"}
        user = {"name": "Alice", "address": addr}
        data = {
            "user": user,
            "backup": user,
            "location": addr,
        }

        encoded = encode_refs(data)

        # Both user and addr should be marked as shared
        assert encoded.count("$") >= 2

    def test_list_of_shared_objects(self) -> None:
        """Handle list containing multiple references to same object."""
        item = {"id": 1}
        data = {"items": [item, item, item]}

        encoded = encode_refs(data)
        decoded = decode_refs(encoded, resolve=True)

        assert decoded["items"][0] is decoded["items"][1]
        assert decoded["items"][1] is decoded["items"][2]

    def test_deeply_nested_references(self) -> None:
        """Handle deeply nested structures with references."""
        shared = {"value": 42}
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "ref1": shared,
                        "ref2": shared,
                    }
                }
            }
        }

        encoded = encode_refs(data)
        decoded = decode_refs(encoded, resolve=True)

        inner = decoded["level1"]["level2"]["level3"]
        assert inner["ref1"] is inner["ref2"]
