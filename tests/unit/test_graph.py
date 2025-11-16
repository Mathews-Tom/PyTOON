"""Unit tests for graph encoding and decoding with circular reference support.

Tests the GraphEncoder.encode_graph() and GraphDecoder.decode_graph()
methods for handling circular references without infinite recursion.
"""

import pytest

from pytoon import decode_graph, encode_graph
from pytoon.references import GraphDecoder, GraphEncoder
from pytoon.utils.errors import TOONDecodeError, TOONEncodeError


class TestEncodeGraphAPI:
    """Tests for the encode_graph() public API."""

    def test_encode_graph_simple_dict(self) -> None:
        """encode_graph handles simple dict without cycles."""
        data = {"a": 1, "b": 2}
        result = encode_graph(data)

        assert "_graph: true" in result
        assert "a: 1" in result
        assert "b: 2" in result

    def test_encode_graph_self_reference(self) -> None:
        """encode_graph handles self-referencing objects."""
        obj: dict[str, object] = {"id": 1}
        obj["self"] = obj

        result = encode_graph(obj)

        assert "_graph: true" in result
        assert "id: 1" in result
        assert "$ref:" in result

    def test_encode_graph_mutual_reference(self) -> None:
        """encode_graph handles mutual circular references."""
        user1: dict[str, object] = {"id": 1, "name": "Alice"}
        user2: dict[str, object] = {"id": 2, "name": "Bob"}
        user1["friend"] = user2
        user2["friend"] = user1

        result = encode_graph({"users": [user1, user2]})

        assert "_graph: true" in result
        assert "$ref:" in result
        # Should have references to break the cycle
        ref_count = result.count("$ref:")
        assert ref_count >= 1

    def test_encode_graph_no_infinite_recursion(self) -> None:
        """encode_graph does not cause infinite recursion on cycles."""
        # Create a circular chain: A -> B -> C -> A
        obj_a: dict[str, object] = {"id": "A"}
        obj_b: dict[str, object] = {"id": "B"}
        obj_c: dict[str, object] = {"id": "C"}
        obj_a["next"] = obj_b
        obj_b["next"] = obj_c
        obj_c["next"] = obj_a

        # This should NOT raise RecursionError
        result = encode_graph(obj_a)

        assert "_graph: true" in result
        assert "$ref:" in result

    def test_encode_graph_primitives(self) -> None:
        """encode_graph handles primitives correctly."""
        assert "null" in encode_graph(None)
        assert "true" in encode_graph(True)
        assert "false" in encode_graph(False)
        assert "42" in encode_graph(42)
        assert "3.14" in encode_graph(3.14)
        assert "hello" in encode_graph("hello")

    def test_encode_graph_empty_list(self) -> None:
        """encode_graph handles empty lists."""
        result = encode_graph([])
        assert "_graph: true" in result
        assert "[0]:" in result

    def test_encode_graph_inline_array(self) -> None:
        """encode_graph generates inline arrays for primitives."""
        result = encode_graph([1, 2, 3])
        assert "_graph: true" in result
        assert "[3]: 1,2,3" in result

    def test_encode_graph_custom_delimiter(self) -> None:
        """encode_graph respects custom delimiter."""
        result = encode_graph([1, 2, 3], delimiter="|")
        assert "[3]: 1|2|3" in result

    def test_encode_graph_nested_structure(self) -> None:
        """encode_graph handles nested structures without cycles."""
        data = {"outer": {"inner": {"value": 42}}}
        result = encode_graph(data)

        assert "_graph: true" in result
        assert "outer:" in result
        assert "inner:" in result
        assert "value: 42" in result

    def test_encode_graph_special_float_values(self) -> None:
        """encode_graph handles NaN and Inf as null."""
        encoder = GraphEncoder()

        nan_result = encoder._encode_value(float("nan"), 0, 2, ",")
        assert nan_result == "null"

        inf_result = encoder._encode_value(float("inf"), 0, 2, ",")
        assert inf_result == "null"

        neg_inf_result = encoder._encode_value(float("-inf"), 0, 2, ",")
        assert neg_inf_result == "null"

    def test_encode_graph_quoted_strings(self) -> None:
        """encode_graph quotes strings that need quoting."""
        data = {"key": "value with, comma"}
        result = encode_graph(data)
        assert '"value with, comma"' in result

    def test_encode_graph_list_with_cycles(self) -> None:
        """encode_graph handles lists containing circular references."""
        obj: dict[str, object] = {"id": 1}
        obj["self"] = obj
        data: dict[str, object] = {"items": [obj, obj]}

        result = encode_graph(data)

        assert "_graph: true" in result
        # Should have references to break cycles
        assert "$ref:" in result


class TestDecodeGraphAPI:
    """Tests for the decode_graph() public API."""

    def test_decode_graph_simple_dict(self) -> None:
        """decode_graph handles simple dict without references."""
        toon = "_graph: true\na: 1\nb: 2"
        result = decode_graph(toon)

        assert result == {"a": 1, "b": 2}

    def test_decode_graph_requires_flag(self) -> None:
        """decode_graph requires _graph: true flag."""
        toon = "a: 1\nb: 2"

        with pytest.raises(TOONDecodeError, match="Expected '_graph: true'"):
            decode_graph(toon)

    def test_decode_graph_self_reference(self) -> None:
        """decode_graph reconstructs self-referencing objects."""
        # Note: $ref:2 refers to the nested obj dict (ID 2)
        # The root dict has ID 1, obj dict has ID 2
        toon = "_graph: true\nobj:\n  id: 1\n  self: $ref:2"
        result = decode_graph(toon)

        assert result["obj"]["self"] is result["obj"]

    def test_decode_graph_mutual_reference(self) -> None:
        """decode_graph reconstructs mutual circular references."""
        # Root dict is ID 1, user1 is ID 2, user2 is ID 3
        toon = """_graph: true
user1:
  id: 1
  friend: $ref:3
user2:
  id: 2
  friend: $ref:2"""
        result = decode_graph(toon)

        assert result["user1"]["friend"] is result["user2"]
        assert result["user2"]["friend"] is result["user1"]

    def test_decode_graph_primitives(self) -> None:
        """decode_graph handles primitive values."""
        assert decode_graph("_graph: true\nvalue: null")["value"] is None
        assert decode_graph("_graph: true\nvalue: true")["value"] is True
        assert decode_graph("_graph: true\nvalue: false")["value"] is False
        assert decode_graph("_graph: true\nvalue: 42")["value"] == 42
        assert decode_graph("_graph: true\nvalue: 3.14")["value"] == 3.14
        assert decode_graph("_graph: true\nvalue: hello")["value"] == "hello"

    def test_decode_graph_quoted_string(self) -> None:
        """decode_graph handles quoted strings."""
        result = decode_graph('_graph: true\nvalue: "hello, world"')
        assert result["value"] == "hello, world"

    def test_decode_graph_inline_array(self) -> None:
        """decode_graph handles inline arrays."""
        toon = "_graph: true\nitems: [3]: 1,2,3"
        result = decode_graph(toon)
        assert result["items"] == [1, 2, 3]

    def test_decode_graph_empty_data(self) -> None:
        """decode_graph handles empty data section."""
        toon = "_graph: true"
        result = decode_graph(toon)
        assert result == {}

    def test_decode_graph_invalid_reference(self) -> None:
        """decode_graph raises error for invalid references."""
        toon = "_graph: true\nobj:\n  ref: $ref:999"

        with pytest.raises(TOONDecodeError, match="Invalid graph reference"):
            decode_graph(toon)

    def test_decode_graph_array_count_validation(self) -> None:
        """decode_graph validates array item count."""
        toon = "_graph: true\nitems: [3]: 1,2"

        with pytest.raises(TOONDecodeError, match="declares 3 items but found 2"):
            decode_graph(toon)

    def test_decode_graph_nested_dict(self) -> None:
        """decode_graph handles nested dictionaries."""
        toon = """_graph: true
outer:
  inner:
    value: 42"""
        result = decode_graph(toon)

        assert result == {"outer": {"inner": {"value": 42}}}

    def test_decode_graph_list_items(self) -> None:
        """decode_graph handles list-style arrays."""
        toon = """_graph: true
items:
  [3]:
  - 1
  - 2
  - 3"""
        result = decode_graph(toon)
        assert result["items"] == [1, 2, 3]


class TestRoundtripFidelity:
    """Tests for encode_graph -> decode_graph roundtrip fidelity."""

    def test_roundtrip_simple_dict(self) -> None:
        """Roundtrip preserves simple dict structure."""
        data = {"name": "Alice", "age": 30}
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        assert decoded == data

    def test_roundtrip_nested_dict(self) -> None:
        """Roundtrip preserves nested dict structure."""
        data = {"user": {"name": "Bob", "metadata": {"level": 1}}}
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        assert decoded == data

    def test_roundtrip_list_of_primitives(self) -> None:
        """Roundtrip preserves list of primitives."""
        data = [1, 2, 3, 4, 5]
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

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
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        assert decoded == data

    def test_roundtrip_circular_reference_structure(self) -> None:
        """Roundtrip preserves circular reference structure."""
        obj: dict[str, object] = {"id": 1, "name": "Test"}
        obj["self"] = obj

        encoded = encode_graph(obj)
        decoded = decode_graph(encoded)

        # Verify circular structure is preserved
        assert decoded["self"] is decoded
        assert decoded["id"] == 1
        assert decoded["name"] == "Test"

    def test_roundtrip_mutual_circular_references(self) -> None:
        """Roundtrip preserves mutual circular references."""
        user1: dict[str, object] = {"id": 1}
        user2: dict[str, object] = {"id": 2}
        user1["friend"] = user2
        user2["friend"] = user1

        data: dict[str, object] = {"user1": user1, "user2": user2}
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        # Verify mutual references
        assert decoded["user1"]["friend"] is decoded["user2"]
        assert decoded["user2"]["friend"] is decoded["user1"]
        assert decoded["user1"]["id"] == 1
        assert decoded["user2"]["id"] == 2

    def test_roundtrip_complex_graph(self) -> None:
        """Roundtrip handles complex graph structures."""
        # Create a more complex graph: A <-> B <-> C, A -> C
        obj_a: dict[str, object] = {"id": "A"}
        obj_b: dict[str, object] = {"id": "B"}
        obj_c: dict[str, object] = {"id": "C"}

        obj_a["b"] = obj_b
        obj_b["a"] = obj_a
        obj_b["c"] = obj_c
        obj_c["b"] = obj_b
        obj_a["c"] = obj_c

        data: dict[str, object] = {"root": obj_a}
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        # Verify structure
        root = decoded["root"]
        assert root["id"] == "A"
        assert root["b"]["id"] == "B"
        assert root["c"]["id"] == "C"
        assert root["b"]["a"] is root
        assert root["b"]["c"] is root["c"]
        assert root["c"]["b"] is root["b"]


class TestCircularReferenceDetection:
    """Tests for circular reference detection and handling."""

    def test_detect_simple_cycle(self) -> None:
        """Detect simple self-referencing cycle."""
        obj: dict[str, object] = {"value": 1}
        obj["self"] = obj

        result = encode_graph(obj)
        assert "$ref:" in result

    def test_detect_two_object_cycle(self) -> None:
        """Detect cycle between two objects."""
        a: dict[str, object] = {"id": "A"}
        b: dict[str, object] = {"id": "B"}
        a["ref"] = b
        b["ref"] = a

        result = encode_graph(a)
        assert "$ref:" in result

    def test_detect_long_cycle(self) -> None:
        """Detect longer circular chains."""
        objects: list[dict[str, object]] = [{"id": i} for i in range(10)]
        for i in range(9):
            objects[i]["next"] = objects[i + 1]
        objects[9]["next"] = objects[0]  # Close the cycle

        result = encode_graph(objects[0])
        assert "$ref:" in result

    def test_no_false_positive_cycles(self) -> None:
        """Non-circular structures should not have $ref."""
        data = {"a": {"b": {"c": 1}}, "d": {"e": 2}}
        result = encode_graph(data)

        # No cycles, so no $ref placeholders
        assert "$ref:" not in result

    def test_shared_but_not_circular(self) -> None:
        """Shared references that are not circular should work."""
        shared = {"value": 42}
        data = {"a": shared, "b": shared}

        result = encode_graph(data)
        # Shared reference will be encoded with $ref since it's seen twice
        assert "$ref:" in result


class TestGraphEncoderMethods:
    """Tests for GraphEncoder methods."""

    def test_assign_ids(self) -> None:
        """_assign_ids assigns unique IDs to all compound objects."""
        encoder = GraphEncoder()
        data = {"outer": {"inner": [1, 2, 3]}}

        encoder._assign_ids(data)

        # Should have IDs for: outer dict, inner dict, list
        assert len(encoder._id_map) == 3

    def test_encode_dict_with_cycle(self) -> None:
        """_encode_dict handles circular references."""
        encoder = GraphEncoder()
        obj: dict[str, object] = {"id": 1}
        obj["self"] = obj

        encoder._assign_ids(obj)
        result = encoder._encode_value(obj, 0, 2, ",")

        assert "$ref:" in result

    def test_encode_list_with_cycle(self) -> None:
        """_encode_list handles circular references."""
        encoder = GraphEncoder()
        lst: list[object] = [1, 2]
        lst.append(lst)  # type: ignore[arg-type]

        encoder._assign_ids(lst)
        result = encoder._encode_value(lst, 0, 2, ",")

        assert "$ref:" in result

    def test_encode_string_quoting(self) -> None:
        """_encode_string handles various string cases."""
        encoder = GraphEncoder()

        # Empty string needs quotes
        assert encoder._encode_string("") == '""'

        # String with comma needs quotes
        assert encoder._encode_string("a,b") == '"a,b"'

        # Simple string doesn't need quotes
        assert encoder._encode_string("hello") == "hello"

    def test_non_string_key_error(self) -> None:
        """_encode_dict raises error for non-string keys."""
        encoder = GraphEncoder()
        data = {123: "value"}  # type: ignore[dict-item]

        encoder._assign_ids(data)
        with pytest.raises(TOONEncodeError, match="keys must be strings"):
            encoder._encode_value(data, 0, 2, ",")

    def test_unsupported_type_error(self) -> None:
        """_encode_value raises error for unsupported types."""
        encoder = GraphEncoder()
        encoder._assign_ids({})

        with pytest.raises(TOONEncodeError, match="Cannot encode type"):
            encoder._encode_value(object(), 0, 2, ",")


class TestGraphDecoderMethods:
    """Tests for GraphDecoder methods."""

    def test_split_inline_array(self) -> None:
        """_split_inline_array handles various cases."""
        decoder = GraphDecoder()

        assert decoder._split_inline_array("1,2,3") == ["1", "2", "3"]
        assert decoder._split_inline_array('"a,b",c') == ['"a,b"', "c"]
        assert decoder._split_inline_array("$ref:1,$ref:2") == ["$ref:1", "$ref:2"]

    def test_unescape_string(self) -> None:
        """_unescape_string handles escape sequences."""
        decoder = GraphDecoder()

        assert decoder._unescape_string("hello") == "hello"
        assert decoder._unescape_string('say \\"hi\\"') == 'say "hi"'
        assert decoder._unescape_string("line\\nbreak") == "line\nbreak"
        assert decoder._unescape_string("tab\\there") == "tab\there"
        assert decoder._unescape_string("back\\\\slash") == "back\\slash"

    def test_decode_value_graph_ref(self) -> None:
        """_decode_value recognizes $ref:N placeholders."""
        decoder = GraphDecoder()
        result = decoder._decode_value("$ref:42")

        assert result == ("__graph_ref__", 42)

    def test_decode_list_lines(self) -> None:
        """_decode_list_lines parses list items correctly."""
        decoder = GraphDecoder()
        lines = ["  - 1", "  - 2", "  - 3"]
        result = decoder._decode_list_lines(lines, 3)
        assert result == [1, 2, 3]

    def test_resolve_placeholders(self) -> None:
        """_resolve_placeholders replaces markers with objects."""
        decoder = GraphDecoder()

        # Set up registry
        obj1 = {"id": 1}
        obj2 = {"id": 2}
        decoder._object_registry = {1: obj1, 2: obj2}

        # Create structure with placeholders
        data = {
            "ref1": ("__graph_ref__", 1),
            "ref2": ("__graph_ref__", 2),
        }

        decoder._resolve_placeholders(data)

        assert data["ref1"] is obj1
        assert data["ref2"] is obj2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_encode_graph_empty_dict(self) -> None:
        """encode_graph handles empty dictionary."""
        result = encode_graph({})
        assert "_graph: true" in result

    def test_encode_graph_empty_nested_dict(self) -> None:
        """encode_graph handles nested empty dictionaries."""
        data = {"outer": {}}
        result = encode_graph(data)
        assert "_graph: true" in result
        assert "outer:" in result

    def test_decode_graph_empty_string(self) -> None:
        """decode_graph handles empty string."""
        with pytest.raises(TOONDecodeError, match="Expected '_graph: true'"):
            decode_graph("")

    def test_decode_graph_whitespace_only(self) -> None:
        """decode_graph handles whitespace-only string."""
        with pytest.raises(TOONDecodeError, match="Expected '_graph: true'"):
            decode_graph("   \n  ")

    def test_decode_graph_boolean_values(self) -> None:
        """decode_graph correctly parses boolean values."""
        result = decode_graph("_graph: true\na: true\nb: false")
        assert result["a"] is True
        assert result["b"] is False

    def test_multiple_self_references(self) -> None:
        """Handle multiple self-referencing objects."""
        obj1: dict[str, object] = {"id": 1}
        obj2: dict[str, object] = {"id": 2}
        obj1["self"] = obj1
        obj2["self"] = obj2

        data = {"obj1": obj1, "obj2": obj2}
        encoded = encode_graph(data)
        decoded = decode_graph(encoded)

        assert decoded["obj1"]["self"] is decoded["obj1"]
        assert decoded["obj2"]["self"] is decoded["obj2"]

    def test_deeply_nested_cycle(self) -> None:
        """Handle cycles in deeply nested structures."""
        root: dict[str, object] = {"level": 0}
        current = root
        for i in range(1, 10):
            next_level: dict[str, object] = {"level": i}
            current["child"] = next_level
            current = next_level
        current["root"] = root  # Create cycle back to root

        encoded = encode_graph(root)
        decoded = decode_graph(encoded)

        # Traverse to the bottom
        node = decoded
        for _ in range(9):
            node = node["child"]  # type: ignore[assignment]

        assert node["root"] is decoded

    def test_graph_encoding_error_handling(self) -> None:
        """encode_graph provides meaningful error messages."""
        encoder = GraphEncoder()

        with pytest.raises(TOONEncodeError, match="Cannot encode type"):
            encoder.encode_graph({"obj": object()})

    def test_graph_decoding_error_handling(self) -> None:
        """decode_graph provides meaningful error messages."""
        # Missing _graph: true flag
        with pytest.raises(TOONDecodeError, match="Expected '_graph: true'"):
            decode_graph("invalid input")

        # Invalid reference
        with pytest.raises(TOONDecodeError, match="Invalid graph reference"):
            decode_graph("_graph: true\nref: $ref:999")


class TestIntegrationWithPublicAPI:
    """Tests for integration with pytoon public API."""

    def test_encode_graph_in_exports(self) -> None:
        """encode_graph is exported from pytoon."""
        from pytoon import encode_graph as api_encode_graph

        result = api_encode_graph({"a": 1})
        assert "_graph: true" in result

    def test_decode_graph_in_exports(self) -> None:
        """decode_graph is exported from pytoon."""
        from pytoon import decode_graph as api_decode_graph

        result = api_decode_graph("_graph: true\na: 1")
        assert result == {"a": 1}

    def test_graph_encoder_in_references_module(self) -> None:
        """GraphEncoder is accessible from pytoon.references."""
        from pytoon.references import GraphEncoder

        encoder = GraphEncoder()
        assert hasattr(encoder, "encode_graph")

    def test_graph_decoder_in_references_module(self) -> None:
        """GraphDecoder is accessible from pytoon.references."""
        from pytoon.references import GraphDecoder

        decoder = GraphDecoder()
        assert hasattr(decoder, "decode_graph")

    def test_all_exports_list(self) -> None:
        """encode_graph and decode_graph are in __all__."""
        import pytoon

        assert "encode_graph" in pytoon.__all__
        assert "decode_graph" in pytoon.__all__


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_social_network_graph(self) -> None:
        """Simulate a social network with friend connections."""
        alice: dict[str, object] = {"name": "Alice", "friends": []}
        bob: dict[str, object] = {"name": "Bob", "friends": []}
        charlie: dict[str, object] = {"name": "Charlie", "friends": []}

        alice["friends"] = [bob, charlie]  # type: ignore[assignment]
        bob["friends"] = [alice, charlie]  # type: ignore[assignment]
        charlie["friends"] = [alice, bob]  # type: ignore[assignment]

        network = {"users": [alice, bob, charlie]}
        encoded = encode_graph(network)
        decoded = decode_graph(encoded)

        # Verify circular structure is maintained
        users = decoded["users"]
        assert users[0]["friends"][0] is users[1]
        assert users[0]["friends"][1] is users[2]
        assert users[1]["friends"][0] is users[0]
        assert users[2]["friends"][1] is users[1]

    def test_tree_with_parent_references(self) -> None:
        """Simulate a tree where nodes have parent references."""
        root: dict[str, object] = {"id": "root", "parent": None, "children": []}
        child1: dict[str, object] = {"id": "child1", "parent": root, "children": []}
        child2: dict[str, object] = {"id": "child2", "parent": root, "children": []}
        grandchild: dict[str, object] = {"id": "grandchild", "parent": child1, "children": []}

        root["children"] = [child1, child2]  # type: ignore[assignment]
        child1["children"] = [grandchild]  # type: ignore[assignment]

        encoded = encode_graph(root)
        decoded = decode_graph(encoded)

        # Verify parent references
        assert decoded["children"][0]["parent"] is decoded
        assert decoded["children"][1]["parent"] is decoded
        assert decoded["children"][0]["children"][0]["parent"] is decoded["children"][0]

    def test_doubly_linked_list(self) -> None:
        """Simulate a doubly linked list structure."""
        node1: dict[str, object] = {"value": 1, "prev": None, "next": None}
        node2: dict[str, object] = {"value": 2, "prev": None, "next": None}
        node3: dict[str, object] = {"value": 3, "prev": None, "next": None}

        node1["next"] = node2
        node2["prev"] = node1
        node2["next"] = node3
        node3["prev"] = node2

        encoded = encode_graph({"head": node1})
        decoded = decode_graph(encoded)

        head = decoded["head"]
        assert head["next"]["prev"] is head
        assert head["next"]["next"]["prev"] is head["next"]
